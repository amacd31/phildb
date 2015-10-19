import os
import sys
import datetime
import pandas as pd
from phildb.database import PhilDB

print("Writing to PhilDB({0})".format(sys.argv[1]))
db = PhilDB(sys.argv[1])
db.add_measurand('maxT', 'MAXIMUM_TEMPERATURE', 'Maximum Temperature')
db.add_measurand('minT', 'MINIMUM_TEMPERATURE', 'Minimum Temperature')
db.add_source('BOM_ACORN_SAT', 'Bureau of Meteorology; Hydrological Reference Stations dataset.')

freq = 'D'

for i in range(2, len(sys.argv)):
    print("Processing file: ", sys.argv[i], '...')
    station_id = "{0:06d}".format(int(os.path.basename(sys.argv[i])))
    print("Using station ID: ", station_id, '...')

    db.add_timeseries(station_id)
    for variable in ['minT', 'maxT']:
        input_file = 'data/acorn.sat.{0}.{1}.daily.txt'.format(variable, station_id)
        df = pd.read_csv(input_file, parse_dates=[0], index_col=0, header=None, skiprows=1, sep=r"\s+", na_values='99999.9', names=['Date',variable])
        db.add_timeseries_instance(station_id, freq, 'ACORN-SAT', measurand = variable, source = 'BOM_ACORN_SAT')
        db.write(station_id, freq, df[variable], measurand = variable, source = 'BOM_ACORN_SAT')

