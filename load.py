import datetime
import json
#from matplotlib import pyplot as plt

from tsdb.writer import TSWriter

def load():
    #return json.load(open('./IDN60903.94926.json'))
    return json.load(open('./data2.json'))


def parse(station_json, measurand):
    dates = []
    data = []
    for ob in station_json['observations']['data']:
        dates.append(
            datetime.datetime.strptime(ob['aifstime_utc'], '%Y%m%d%H%M%S')
        )
        data.append(ob[measurand])

    return dates, data


def write(measurand='air_temp'):
    x = parse(load(), measurand)

    with TSWriter('test.hdf5', 'a') as writer:
        #writer.create_skeleton()
        for date, value in zip(x[0], x[1]):
            writer.write(date, value)

write()


#def plot_data(measurand='air_temp'):
    #x = parse(load(), measurand)
    #plt.plot(x[0], x[1])
    #plt.show()
