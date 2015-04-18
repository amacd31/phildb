from struct import unpack, calcsize
import numpy as np
import pandas as pd
import os

from tsdb.constants import METADATA_MISSING_VALUE

def __read(filename):
    field_names = ['date', 'value', 'metaID']
    entry_format = 'ldi' # long, double, int; See field names above.
    entry_size = calcsize(entry_format)

    records = np.fromfile(filename, dtype=np.dtype({'names':field_names, 'formats': entry_format}))

    if records == []: return pd.DataFrame(None, columns = ['date', 'value', 'metaID'])

    df = pd.DataFrame(records, columns = field_names)
    df['date'] = pd.to_datetime(df['date'], unit='s')
    df = df.set_index('date')

    meta_ids = df.metaID
    df.loc[df.metaID == METADATA_MISSING_VALUE] = np.nan
    df.metaID = meta_ids

    return df

def read(filename):
    return __read(filename).value

