from . import reader
from . import writer
import config

def bulk_write(timeseries_id, x):
    return writer.bulk_write(config.tsdb_path, timeseries_id, x)

def write(timeseries_id, x):
    return writer.write(config.tsdb_path, timeseries_id, x)

def read_all(timeseries_id):
    return reader.read_all(config.tsdb_path, timeseries_id)

