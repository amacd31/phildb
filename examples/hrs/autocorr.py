import sys

import numpy as np
from tsdb.database import TSDB

db = TSDB(sys.argv[1])

ac = np.array(
        [ (hrs_id, db.read_all(hrs_id, 'D', measurand = 'Q', source = 'BOM_HRS').value.autocorr()) for hrs_id in db.list()],
        dtype = [('name','S8'),('val',float)]
        )


for station in ac[ac['val'] >= 0.95]:
    print station['name'], station['val']
