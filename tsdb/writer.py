import calendar
import os
import struct

def bulk_write(tsdb_path, timeseries_id, x):
    """
        Good for initial bulk load. Expects continuous time series.
    """
    with open(os.path.join(tsdb_path, timeseries_id + '.tsdb'), 'wb') as writer:
        for date, value in zip(x[0], x[1]):
            data = struct.pack('ldi', calendar.timegm(date.utctimetuple()), value, 0)
            writer.write(data)

def write(tsdb_path, timeseries_id, x):
    """
        Good for initial bulk load. Expects continuous time series.
    """
    start_date = x[0]
    end_date = x[-1]

    delta = start_date - end_date
    assert delta.days == len(x)

    with open(os.path.join(tsdb_path, timeseries_id + '.tsdb'), 'wb') as writer:
        for date, value in zip(x[0], x[1]):
            data = struct.pack('ldi', calendar.timegm(date.utctimetuple()), value, 0)
            writer.write(data)
