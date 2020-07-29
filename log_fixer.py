"""
    This script is used to fix up log files that were created prior
    to PhilDB version v0.6.1-6-g2d12eed.

    It takes a list of log files (without the .hdf5 extension) as arguments.

    The script will then move each .hdf5 file to .original_hdf5 and process the
    data in .original_hdf5 into a new .hdf5 with fixed up dates.

    The script assumes any date after 2030 is the result of the wrap around bug
    and will attempt to fix it. Any date before that will be returned as is.

    For example within the data directory of a phildb instance (i.e. where the
    log .hdf5 files are) run:

        python log_fixer.py $(ls -1 *.hdf5 | cut -d'.' -f1)

    As with most things if you care about your data you should make backups
    before running this script.
"""
import calendar
import numpy as np
import os
import sys

from datetime import datetime
from pandas import Timestamp

from phildb.constants import MISSING_VALUE, METADATA_MISSING_VALUE
from phildb.log_handler import LogHandler


class FixLogHandler(LogHandler):
    def write_data(self, data):

        ts_table = self.hdf5.get_node("/data/log")

        index_row = ts_table.row
        for dt, data in data.iterrows():
            if data[0] is np.nan:
                data[0] = MISSING_VALUE
                data[1] = METADATA_MISSING_VALUE

            index_row["time"] = calendar.timegm(dt.to_pydatetime().utctimetuple())
            index_row["value"] = data[0]
            index_row["meta"] = data[1]
            index_row["replacement_time"] = calendar.timegm(
                data[2].to_pydatetime().utctimetuple()
            )
            index_row.append()

        self.hdf5.flush()


def fix_index(dt):
    if dt < Timestamp("2030-03-01"):
        return dt

    orig_int = calendar.timegm(dt.to_pydatetime().utctimetuple())

    # (INT_MAX - orig_int) gives how much we overflowed by
    # We can then subract (2147483647 - orig_int) from (INT_MIN - 1)
    # to get the integer we were supposed to have before the overflow.
    new_int = -2147483649 - (2147483647 - orig_int)

    return datetime.utcfromtimestamp(new_int)


for hashname in sys.argv[1:]:

    os.rename(hashname + ".hdf5", hashname + ".original_hdf5")

    with LogHandler(hashname + ".original_hdf5", "r") as orig:
        original_log = orig.read(calendar.timegm(datetime(9999, 1, 1).utctimetuple()))

    df = original_log.reset_index()
    original_log.index = df["date"].apply(fix_index)

    with FixLogHandler(hashname + ".hdf5", "w") as n:
        n.create_skeleton()
        n.write_data(original_log)
