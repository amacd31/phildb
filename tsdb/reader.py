from struct import unpack, calcsize
import numpy as np
import pandas as pd
import os

from tsdb.constants import METADATA_MISSING_VALUE

def read_all(filename):
    field_names = ['date', 'value', 'metaID']
    entry_format = 'ldi' # long, double, int; See field names above.
    entry_size = calcsize(entry_format)

    records = np.fromfile(filename, dtype=np.dtype({'names':field_names, 'formats': entry_format}))

    if records == []: return pd.DataFrame(None, columns = ['date', 'value', 'metaID'])

    df = pd.DataFrame(records, columns = field_names)
    df['date'] = pd.to_datetime(df['date'], unit='s')
    df = df.set_index('date')

    df.value.loc[df.metaID == METADATA_MISSING_VALUE] = np.nan

    return df

