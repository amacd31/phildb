import calendar
import os
import numpy as np
import tables
from datetime import datetime, date

class TabDesc(tables.IsDescription):
    time = tables.Int32Col(dflt=0, pos=0)
    isotime = tables.StringCol(26)
    value = tables.Float64Col(dflt=np.nan, pos=1)

class TSWriter:
    """
    """

    def __init__(self, filename, mode):
        self.hdf5 = tables.openFile(filename, mode)

    def create_skeleton(self):
        """Create the skeleton of the data self.hdf5.
        """
        metaData = self.hdf5.createArray(
            "/", "meta", 0, "meta data. see its attributes."
        )
        metaData.attrs.creationDate = datetime.now().isoformat()
        metaData.attrs.recentRevisionDate = datetime.now().isoformat()
        metaData.attrs.referenceTime = date.fromordinal(1).isoformat()

        data_group = self.hdf5.createGroup('/', 'data', 'data group')
        self.hdf5.createGroup(data_group, 'timeseries', 'time series data')

        self.hdf5.flush()

    def write(self, date, value):

        root = self.hdf5.getNode('/data/timeseries')

        try:
            self.hdf5.createGroup(root,
                     'Y' + str(date.year)
                )
        except tables.exceptions.NodeError, e:
            pass

        year_group = self.hdf5.getNode('/data/timeseries/Y' + str(date.year))

        try:
            new_table = self.hdf5.createTable(year_group,
                     'M' + str(date.month),
                     TabDesc
                )
            new_table.cols.time.create_index()
            new_table.cols.isotime.create_index()
        except tables.exceptions.NodeError, e:
            pass

        month_table = self.hdf5.getNode('/data/timeseries/Y' + str(date.year) + '/M' + str(date.month))

        query = '(time == %d)' % (calendar.timegm(date.utctimetuple()))
        result = month_table.get_where_list(query)
        if len(result) == 0:
            indexRow = month_table.row
            indexRow["time"] = calendar.timegm(date.utctimetuple())
            indexRow["isotime"] = date.isoformat()
            indexRow["value"] = value
            indexRow.append()

            self.hdf5.root.meta.attrs.recentRevisionDate = \
                datetime.now().isoformat()
        elif len(result) > 1:
            pass

        self.hdf5.flush()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__del__()

    def __del__(self):
        if self.hdf5 is not None:
            self.hdf5.close()
            self.hdf5 = None

    def __str__(self):
        return str(self.hdf5)
