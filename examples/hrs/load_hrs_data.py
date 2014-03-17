import os
import sys
import datetime
import pandas
from tsdb.database import TSDB

print "Writing to TSDB({0})".format(sys.argv[1])
db = TSDB(sys.argv[1])
db.add_measurand('Q', 'STREAMFLOW', 'Streamflow')

for i in range(2, len(sys.argv)):
    print "Processing file: ", sys.argv[i], '...'
    station_id = os.path.basename(sys.argv[i]).split('_')[0]
    print "Using station ID: ", station_id, '...'
    try:
        df = pandas.read_csv(sys.argv[i], parse_dates=True, index_col='Date', skiprows=18)
        db.add_timeseries(station_id)
        db.bulk_write(station_id, 'Q', (df.index, df['Q'].values))
    except ValueError, e:
        print "Skipping unloadable text file: ", sys.argv[i]
        pass

