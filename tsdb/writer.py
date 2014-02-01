import calendar
import os
import struct

import config

def bulk_write(timeseries_id, x):
    """
        Good for initial bulk load. Expects continuous time series.
    """
    with open(os.path.join(config.tsdb_path, timeseries_id + '.tsdb'), 'wb') as writer:
        for date, value in zip(x[0], x[1]):
            data = struct.pack('ldi', calendar.timegm(date.utctimetuple()), value, 0)
            writer.write(data)

