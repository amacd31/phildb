import calendar
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import os
import pandas as pd
from struct import pack, unpack, calcsize

from tsdb.constants import MISSING_VALUE, METADATA_MISSING_VALUE
from tsdb.log_handler import LogHandler
from tsdb.exceptions import DataError
from tsdb.reader import __read, read

field_names = ['date', 'value', 'metaID']
entry_format = 'ldi' # long, double, int; See field names above.
entry_size = calcsize(entry_format)

def __convert_and_validate(ts, freq):
    """
        Turn tuple of (dates, values) into a pandas TimeSeries.

        Validates the input is sensible (e.g. consecutive values).

        :param ts: Tuple of (dates, values)
        :type ts: (np.ndarray, np.ndarray)
    """
    # Convert all to datetime when utctimetuple is not available (i.e. date object).
    for i in range(0, len(ts[0])):
        if 'utctimetuple' not in dir(ts[0][i]):
            ts[0][i] = dt.fromordinal(ts[0][i].toordinal())

    cur_date = ts[0][0]
    for the_date in ts[0][1:]:
        if cur_date >= the_date:
            raise DataError('Unordered dates were supplied. {0} >= {1}'. \
                    format(cur_date, the_date))
        cur_date = the_date

    if freq == 'IRR':
        series = pd.TimeSeries(ts[1], index=ts[0])
    else:
        series = pd.TimeSeries(ts[1], index=ts[0]).asfreq(freq)

    return series


def write(tsdb_file, ts, freq):
    """
        Smart write.

        Will only update existing values where they have changed.
        Changed existing values are returned in a list.

        :param tsdb_file: File to write timeseries data into.
        :type tsdb_file: string
        :param ts: Tuple of (dates, values).
        :type ts: (np.ndarray, np.ndarray)
        :param freq: Frequency of the data. (e.g. 'D' for daily, '1Min' for minutely).
            Accepts any string that pandas.TimeSeries.asfreq does or 'IRR' for irregular data.
        :type freq: string
    """

    series = __convert_and_validate(ts, freq)

    # If the file didn't exist it is a straight foward write and we can
    # just return at the end of this if block.
    if not os.path.isfile(tsdb_file):
        df = pd.DataFrame({'value': series.values, 'metaID': [0] * len(series)}, index = series.index)
        df.index.name = 'date'
        df.to_csv(tsdb_file)

        return [] # No modified entries.

    # If we reached here it wasn't a straight write to a new file.
    existing = __read(tsdb_file)

    overlap_idx = existing.index.intersection(series.index)
    modified = series.ix[overlap_idx] != existing.value.ix[overlap_idx]
    records_to_modify = existing.loc[overlap_idx].ix[modified.values]

    modified_entries = []
    for date, value, meta_id in zip(records_to_modify.index, records_to_modify.value, records_to_modify.metaID):
        modified_entries.append((calendar.timegm(date.utctimetuple()), value, meta_id))

    # combine_first does not preserve null values in the original series.
    # So do an initial merge.
    merged = series.combine_first(existing.value)
    default_meta = pd.Series([0]*len(merged), index = merged.index)
    merged_meta = default_meta.combine_first(existing.metaID)

    # Then replace the null values from the update series.
    null_vals = series.isnull()
    null_idx = null_vals.loc[null_vals==True].index
    merged.loc[null_idx] = np.nan

    os.rename(tsdb_file, tsdb_file + 'backup')

    try:
        df = pd.DataFrame({'value': merged.values, 'metaID': merged_meta.values}, index = merged.index)
        if freq != 'IRR':
            df = df.asfreq(freq)
        df.metaID[df.value.isnull()] = METADATA_MISSING_VALUE
        df.index.name = 'date'
        df.to_csv(tsdb_file)
    except e:
        # On any failure writing restore the original file.
        os.rename(tsdb_file + 'backup', tsdb_file)
        # Then re-raise the exception
        raise e
    else:
        # On successfull write remove the original file.
        os.unlink(tsdb_file + 'backup')

    return modified_entries

def write_log(log_file, modified, replacement_datetime):

    if not os.path.exists(log_file):
        with LogHandler(log_file, 'w') as writer:
            writer.create_skeleton()

    with LogHandler(log_file, 'a') as writer:
        writer.write(modified, calendar.timegm(replacement_datetime.utctimetuple()))
