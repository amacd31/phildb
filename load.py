import sys

import datetime
import json
#from matplotlib import pyplot as plt

from tsdb.writer import TSWriter

def load(input_file):
    #return json.load(open('./IDN60903.94926.json'))
    return json.load(open(input_file))


def parse(station_json, measurand):
    dates = []
    data = []
    for ob in station_json['observations']['data']:
        dates.append(
            datetime.datetime.strptime(ob['aifstime_utc'], '%Y%m%d%H%M%S')
        )
        data.append(ob[measurand])

    return dates, data

def new_file():
    with TSWriter('test.hdf5', 'w') as writer:
        writer.create_skeleton()

def write(x):

    with TSWriter('test.hdf5', 'a') as writer:
        for date, value in zip(x[0], x[1]):
            writer.write(date, value)

new_file()
measurand='air_temp'
print len(sys.argv)
for i in range(1, len(sys.argv)):
    print "Processing file: ", sys.argv[i], '...'
    try:
        x = parse(load(sys.argv[i]), measurand)
        write(x)
    except ValueError, e:
        print "Skipping unloadable json file: ", sys.argv[i]
        pass


#def plot_data(measurand='air_temp'):
    #x = parse(load(), measurand)
    #plt.plot(x[0], x[1])
    #plt.show()
