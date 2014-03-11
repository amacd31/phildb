from datetime import datetime
import md5
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound
Session = sessionmaker()

from . import constants
from . import reader
from . import writer
from .dbstructures import SchemaVersion, Timeseries, Measurand

class TSDB(object):
    def __init__(self, tsdb_path):
        self.tsdb_path = tsdb_path

        if not os.path.exists(self.tsdb_path):
            raise IOError("TSDB doesn't exist ({0})".format(self.tsdb_path))

        if not os.path.exists(self.__meta_data_db()):
            raise IOError("TSDB doesn't contain meta-database ({0})".format(self.__meta_data_db()))

        self.__engine = create_engine('sqlite:///{0}'.format(self.__meta_data_db()))
        Session.configure(bind=self.__engine)

        assert self.version() == "0.0.2";

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

    def add_timeseries(self, identifier):
        the_id = identifier.strip()
        session = Session()
        ts = Timeseries(primary_id = identifier, timeseries_id = md5.md5(identifier).hexdigest())
        session.add(ts)
        session.commit()

    def add_measurand(self, measurand_short_id, measurand_long_id, description):
        short_id = measurand_short_id.strip().upper()
        long_id = measurand_long_id.strip().upper()
        session = Session()
        measurand = Measurand(short_id = short_id, long_id = long_id,  description = description)
        session.add(measurand)
        session.commit()

    def __get_record_by_id(self, identifier):
        session = Session()
        query = session.query(Timeseries).filter(Timeseries.primary_id == identifier)
        try:
            record = query.one()
        except MultipleResultsFound, e:
            raise e

        return record

    def __get_tsdb_file_by_id(self, identifier, ftype='tsdb'):
        record = self.__get_record_by_id(identifier)
        return os.path.join(self.__data_dir(), record.timeseries_id + '.' + ftype)

    def bulk_write(self, identifier, ts):
        writer.bulk_write(self.__get_tsdb_file_by_id(identifier), ts)

    def write(self, identifier, ts):
        modified = writer.write(self.__get_tsdb_file_by_id(identifier), ts)

        log_file = self.__get_tsdb_file_by_id(identifier, 'hdf5')

        writer.write_log(log_file, modified, datetime.utcnow())

    def read_all(self, identifier):
        return reader.read_all(self.__get_tsdb_file_by_id(identifier))

    def __str__(self):
        return self.tsdb_path
