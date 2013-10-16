import calendar
import os
import numpy as np
import tables
import pandas as pd
from datetime import datetime, date

class TabDesc(tables.IsDescription):
    time = tables.Int32Col(dflt=0, pos=0)
    isotime = tables.StringCol(26)
    value = tables.Float64Col(dflt=np.nan, pos=1)

class TSReader:
    """
    """

    def __init__(self, filename, mode):
        self.hdf5 = tables.openFile(filename, mode)

    def read(self, start_date, end_date):

        start_year = start_date.year
        end_year = end_date.year

        ts_table = self.hdf5.getNode('/data/timeseries')

        query = '(time >= %d) & (time <= %d)' % (calendar.timegm(start_date.utctimetuple()), calendar.timegm(end_date.utctimetuple()))

        df = pd.DataFrame(ts_table.read_where(query))
        df.index = pd.to_datetime(df['isotime'])
        ts = df['value']

        return ts

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
