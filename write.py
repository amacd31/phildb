import sys
import datetime
import pandas
from tsdb.writer import bulk_write

#print "Processing file: ", sys.argv[1], '...'
#x = pandas.read_csv(sys.argv[1], parse_dates={'datetime': [2,3,4]}, index_col='datetime')
#write((x.index, x['Minimum temperature (Degree C)'].values))

for i in range(2, len(sys.argv)):
    print "Processing file: ", sys.argv[i], '...'
    try:
        df = pandas.read_csv(sys.argv[i], parse_dates=True, index_col='Date', skiprows=18)
        bulk_write(sys.argv[i], (df.index, df['Q'].values))
    except ValueError, e:
        print "Skipping unloadable text file: ", sys.argv[i]
        pass

