import os
import sys
import datetime
import json
import pandas
from tsdb.database import TSDB

db = TSDB(sys.argv[1])

def parse(station_json, measurand):
    dates = []
    data = []
    for ob in station_json['observations']['data']:
        the_date = datetime.datetime.strptime(ob['aifstime_utc'], '%Y%m%d%H%M%S')
        if the_date.minute == 0 or the_date.minute == 30:
            dates.append(the_date)
            data.append(ob[measurand])
    dates.reverse()
    data.reverse()

    with open("input.txt", "a") as myfile:
        for date, value in zip(dates, data):
            myfile.write("{0}, {1}\n".format(date.isoformat(), value))

    station_id = station_json['observations']['header'][0]['ID']

    return station_id, dates, data

measurand = 'air_temp'
source = 'BOM_OBS'
freq = '30min'

station_id, dates, data = parse(json.load(open(sys.argv[2])), measurand)

db.add_measurand(measurand, measurand, 'Air Temperature')
db.add_source('BOM_OBS', 'Australian Bureau of Meteorology Observations')

db.add_timeseries(station_id)
db.add_timeseries_instance(station_id, freq, 'None', measurand = measurand, source = source)
db.write(station_id, freq, (dates, data), measurand = measurand, source = source)

for i in range(3, len(sys.argv)):
    print("Processing file: ", sys.argv[i], '...')

    try:
        x = parse(json.load(open(sys.argv[i])), measurand)
        db.write(station_id, freq, x, measurand = measurand, source = source)
    except ValueError as e:
        print('Could not parse: {0}'.format(sys.argv[i]))

