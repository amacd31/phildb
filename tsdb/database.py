import os
import sqlite3

from . import reader
from . import writer

class TSDB(object):
    def __init__(self, tsdb_path):
        self.tsdb_path = tsdb_path

        if not os.path.exists(self.tsdb_path):
            raise IOError("TSDB doesn't exist ({0})".format(self.tsdb_path))

        if not os.path.exists(self.__meta_data_db()):
            raise IOError("TSDB doesn't contain meta-database ({0})".format(self.__meta_data_db()))

        assert self.version() == 1;

    def __meta_data_db(self):
        return os.path.join(self.tsdb_path, 'tsdb.sqlite')

    def __data_dir(self):
        return os.path.join(self.tsdb_path, 'data')

    def version(self):
        conn = sqlite3.connect(self.__meta_data_db())
        c = conn.cursor()
        c.execute("PRAGMA user_version;")
        version = c.fetchone()[0];

        return version

