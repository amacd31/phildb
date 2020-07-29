import calendar
from struct import unpack, calcsize
import numpy as np
import pandas as pd
import os

from phildb.constants import METADATA_MISSING_VALUE
from phildb.log_handler import LogHandler


def __read(filename):
    field_names = ["date", "value", "metaID"]
    entry_format = "<qdi"  # long, double, int; See field names above.
    entry_size = calcsize(entry_format)

    if not os.path.exists(filename):
        return pd.DataFrame(None, columns=["date", "value", "metaID"])

    records = np.fromfile(
        filename, dtype=np.dtype({"names": field_names, "formats": entry_format[1:]})
    )

    if len(records) == 0:
        return pd.DataFrame(None, columns=["date", "value", "metaID"])

    df = pd.DataFrame(records, columns=field_names)
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df = df.set_index("date")

    meta_ids = df.metaID
    df.loc[df.metaID == METADATA_MISSING_VALUE] = np.nan
    df.metaID = meta_ids

    return df


def read(filename):
    return __read(filename).value


def read_log(log_file, as_at_datetime):

    with LogHandler(log_file, "r") as reader:
        df = reader.read(calendar.timegm(as_at_datetime.utctimetuple()))

    return df.value
