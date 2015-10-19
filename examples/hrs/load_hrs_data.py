import os
import sys
import datetime
import pandas
from phildb.database import PhilDB

print("Writing to PhilDB({0})".format(sys.argv[1]))
db = PhilDB(sys.argv[1])
db.add_measurand('Q', 'STREAMFLOW', 'Streamflow')
db.add_source('BOM_HRS', 'Bureau of Meteorology; Hydrological Reference Stations dataset.')

freq = 'D'

hrs_header_len = 18

for i in range(2, len(sys.argv)):
    print("Processing file: ", sys.argv[i], '...')
    station_id = os.path.basename(sys.argv[i]).split('_')[0]
    print("Using station ID: ", station_id, '...')
    try:
        with open(sys.argv[i]) as datafile:
            header=[next(datafile) for x in range(hrs_header_len)]
        header = ''.join(header)
        df = pandas.read_csv(sys.argv[i], parse_dates=True, index_col='Date', skiprows=hrs_header_len)
        db.add_timeseries(station_id)
        db.add_timeseries_instance(station_id, freq, header, measurand = 'Q', source = 'BOM_HRS')
        db.write(station_id, freq, df['Q'], measurand = 'Q', source = 'BOM_HRS')
    except ValueError as e:
        print("Skipping unloadable text file: ", sys.argv[i])
        pass

