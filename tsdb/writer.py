import calendar
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import os
from struct import pack, unpack, calcsize

from .constants import MISSING_VALUE, METADATA_MISSING_VALUE
from .log_handler import LogHandler

field_names = ['date', 'value', 'metaID']
entry_format = 'ldi' # long, double, int; See field names above.
entry_size = calcsize(entry_format)

def __pack(record_date, value, default_flag=0):

    if np.isnan(value):
        data = pack('ldi',
                    record_date,
                    MISSING_VALUE,
                    METADATA_MISSING_VALUE)
    else:
        data = pack('ldi', record_date, value, default_flag)

    return data

def bulk_write(tsdb_file, x):
    """
        Good for initial bulk load. Expects continuous time series.
    """
    with open(tsdb_file, 'wb') as writer:
        for date, value in zip(x[0], x[1]):
            # Convert to datetime when utctimetuple is not available (i.e. date object).
            if 'utctimetuple' not in dir(date):
                date = dt.fromordinal(date.toordinal())
            datestamp = calendar.timegm(date.utctimetuple())
            data = __pack(datestamp, value)
            writer.write(data)

def write(tsdb_file, ts):
    """
        Smart write. Expects continuous time series.

        Will only update existing values where they have changed.
        Changed existing values are returned in a list.
    """
    # Convert all to datetime when utctimetuple is not available (i.e. date object).
    for i in xrange(0, len(ts[0])):
        if 'utctimetuple' not in dir(ts[0][i]):
            ts[0][i] = dt.fromordinal(ts[0][i].toordinal())

    start_date = ts[0][0]
    end_date = ts[0][-1]

    assert (end_date - start_date).days + 1 == len(ts[0])

    cur_date = ts[0][0]
    for the_date in ts[0][1:]:
        if cur_date >= the_date:
            raise ValueError('Unordered dates were supplied. {0} >= {1}'. \
                    format(cur_date, the_date))
        cur_date = the_date

    with open(tsdb_file, 'rb') as reader:
        first_record = unpack(entry_format, reader.read(entry_size))
        reader.seek(entry_size * -1, os.SEEK_END)
        last_record = unpack(entry_format, reader.read(entry_size))

    first_record_date = dt.utcfromtimestamp(first_record[0])
    last_record_date = dt.utcfromtimestamp(last_record[0])
    modified_entries = []

    # We are updating existing data
    if start_date <= last_record_date:
        offset = (start_date - first_record_date).days

        with open(tsdb_file, 'r+b') as writer:
            # If we write past the end of the file
            records = []
            if end_date >= last_record_date:
                # Read until the eof for comparisons
                writer.seek(entry_size * offset, os.SEEK_SET)

                for record in iter(lambda: writer.read(entry_size), ""):
                    records.append(unpack(entry_format, record))
            elif end_date < last_record_date and end_date >= first_record_date:
                # Read overlapping for comparisons
                writer.seek(entry_size * offset, os.SEEK_SET)

                for record in iter(lambda: writer.read(entry_size), ""):
                    records.append(unpack(entry_format, record))

            records_length = len(records)

            # Start a count for records from the starting write position
            rec_count = 0
            writer.seek(entry_size * offset, os.SEEK_SET)
            for date, value in zip(ts[0], ts[1]):
                datestamp = calendar.timegm(date.utctimetuple())
                overlapping = rec_count <= records_length - 1
                if overlapping and records[rec_count][1] == value:
                    # Skip writing the entry if it hasn't changed.
                    writer.seek(entry_size * (rec_count +1) + (entry_size * offset), os.SEEK_SET)
                elif overlapping and records[rec_count][1] != value:
                    modified_entries.append(records[rec_count])
                    data = __pack(datestamp, value)
                    writer.write(data)
                else:
                    data = __pack(datestamp, value)
                    writer.write(data)
                rec_count += 1

    # We are appending data
    elif start_date > last_record_date and (start_date - last_record_date).days == 1:
        with open(tsdb_file, 'ab') as writer:
            for date, value in zip(ts[0], ts[1]):
                datestamp = calendar.timegm(date.utctimetuple())
                data = __pack(datestamp, value)
                writer.write(data)
    elif start_date > last_record_date and (start_date - last_record_date).days > 1:
        with open(tsdb_file, 'a+b') as writer:
            delta_days = (start_date - last_record_date).days
            for day in xrange(1, delta_days):
                the_date = last_record_date + relativedelta(days=day)
                data = pack('ldi',
                            calendar.timegm(the_date.utctimetuple()),
                                            MISSING_VALUE,
                                            METADATA_MISSING_VALUE)
                writer.write(data)
            for date, value in zip(ts[0], ts[1]):
                datestamp = calendar.timegm(date.utctimetuple())
                data = __pack(datestamp, value)
                writer.write(data)
    else: # Not yet supported
        raise NotImplementedError

    return modified_entries

def write_log(log_file, modified, replacement_datetime):

    if not os.path.exists(log_file):
        with LogHandler(log_file, 'w') as writer:
            writer.create_skeleton()

    with LogHandler(log_file, 'a') as writer:
        writer.write(modified, calendar.timegm(replacement_datetime.utctimetuple()))
