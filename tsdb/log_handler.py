import numpy as np
import tables

class TabDesc(tables.IsDescription):
    time = tables.Int32Col(dflt=0, pos=0)
    value = tables.Float64Col(dflt=np.nan, pos=1)
    meta = tables.Int32Col(dflt=0, pos=2)
    replacement_time = tables.Int32Col(dflt=0, pos=3)

class LogHandler:
    """
    """

    def __init__(self, filename, mode):
        self.hdf5 = tables.openFile(filename, mode, complib='blosc')

    def create_skeleton(self):
        """
            Create the skeleton of the data self.hdf5.
        """
        data_group = self.hdf5.createGroup('/', 'data', 'data group')

        try:
            new_table = self.hdf5.createTable(data_group,
                     'log',
                     TabDesc
                )
        except tables.exceptions.NodeError as e:
            pass

        self.hdf5.flush()

    def write(self, modified, replacement_datetime):

        ts_table = self.hdf5.getNode('/data/log')

        index_row = ts_table.row
        for dt, val, meta in iter(modified):
            index_row["time"] = dt
            index_row["value"] = val
            index_row["meta"] = meta
            index_row["replacement_time"] = replacement_datetime
            index_row.append()

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
