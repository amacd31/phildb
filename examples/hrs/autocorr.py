import sys

import numpy as np
from phildb.database import PhilDB

db = PhilDB(sys.argv[1])

ac = np.array(
    [
        (hrs_id, db.read(hrs_id, "D", measurand="Q", source="BOM_HRS").autocorr())
        for hrs_id in db.ts_list()
    ],
    dtype=[("name", "S8"), ("val", float)],
)


for station in ac[ac["val"] >= 0.95]:
    print(station["name"], station["val"])
