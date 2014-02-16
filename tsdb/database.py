import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound
Session = sessionmaker()

from . import constants
from . import reader
from . import writer
from .dbstructures import SchemaVersion

class TSDB(object):
    def __init__(self, tsdb_path):
        self.tsdb_path = tsdb_path

        if not os.path.exists(self.tsdb_path):
            raise IOError("TSDB doesn't exist ({0})".format(self.tsdb_path))

        if not os.path.exists(self.__meta_data_db()):
            raise IOError("TSDB doesn't contain meta-database ({0})".format(self.__meta_data_db()))

        self.__engine = create_engine('sqlite:///{0}'.format(self.__meta_data_db()), echo=True)
        Session.configure(bind=self.__engine)

        assert self.version() == "0.0.1";

    def __meta_data_db(self):
        return os.path.join(self.tsdb_path, constants.METADATA_DB)

    def __data_dir(self):
        return os.path.join(self.tsdb_path, 'data')

    def version(self):
        session = Session()
        query = session.query(SchemaVersion.version)

        try:
            version = query.scalar()
        except MultipleResultsFound, e:
            raise e

        return version

