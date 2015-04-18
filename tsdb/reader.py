from struct import unpack, calcsize
import numpy as np
import pandas as pd
import os

from tsdb.constants import METADATA_MISSING_VALUE

def __read(filename):
    field_names = ['date', 'value', 'metaID']
    entry_format = 'ldi' # long, double, int; See field names above.
    entry_size = calcsize(entry_format)

    if os.path.getsize(filename) > 0:
        df = pd.read_csv(filename, index_col = 'date', parse_dates = True)
    else:
        return pd.DataFrame(None, columns = ['date', 'value', 'metaID'])

    meta_ids = df.metaID.copy()
    df.loc[df.metaID == METADATA_MISSING_VALUE] = np.nan
    df.metaID = meta_ids

    return df

def read(filename):
    return __read(filename).value

