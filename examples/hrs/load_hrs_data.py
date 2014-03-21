import os
import sys
import datetime
import pandas
from tsdb.database import TSDB

print "Writing to TSDB({0})".format(sys.argv[1])
db = TSDB(sys.argv[1])
db.add_measurand('Q', 'STREAMFLOW', 'Streamflow')
db.add_source('BOM_HRS', 'Bureau of Meteorology; Hydrological Reference Stations dataset.')

hrs_header_len = 18

for i in range(2, len(sys.argv)):
    print "Processing file: ", sys.argv[i], '...'
    station_id = os.path.basename(sys.argv[i]).split('_')[0]
    print "Using station ID: ", station_id, '...'
    try:
        with open(sys.argv[i]) as datafile:
            header=[datafile.next() for x in xrange(hrs_header_len)]
        header = ''.join(header)
        df = pandas.read_csv(sys.argv[i], parse_dates=True, index_col='Date', skiprows=hrs_header_len)
        db.add_timeseries(station_id)
        db.add_timeseries_instance(station_id, 'Q', 'BOM_HRS', header)
        db.bulk_write(station_id, 'Q', (df.index, df['Q'].values), 'BOM_HRS')
    except ValueError, e:
        print "Skipping unloadable text file: ", sys.argv[i]
        pass

