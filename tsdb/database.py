from datetime import datetime
import md5
import os
import types

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
Session = sessionmaker()

import logging
logger = logging.getLogger('TSDB_database')

from . import constants
from . import reader
from . import writer
from .dbstructures import SchemaVersion, Timeseries, Measurand

class TSDB(object):
    def __init__(self, tsdb_path):
        self.tsdb_path = tsdb_path

        logger.debug(self.__meta_data_db())

        if not os.path.exists(self.tsdb_path):
            raise IOError("TSDB doesn't exist ({0})".format(self.tsdb_path))

        if not os.path.exists(self.__meta_data_db()):
            raise IOError("TSDB doesn't contain meta-database ({0})".format(self.__meta_data_db()))

        self.__engine = create_engine('sqlite:///{0}'.format(self.__meta_data_db()))
        Session.configure(bind=self.__engine)

        assert self.version() == constants.DB_VERSION;

    def __meta_data_db(self):
        return os.path.join(self.tsdb_path, constants.METADATA_DB)

    def __data_dir(self):
        return os.path.join(self.tsdb_path, 'data')

    def help(self):
        """
            List methods of the TSDB class with the first line of their docstring.
        """
        for method in sorted(dir(self)):
            if method.startswith("_"):
                continue
            if not isinstance(getattr(self, method), types.MethodType):
                continue

            docstring = getattr(self, method).__doc__
            if docstring is None:
                short_string = ''
            else:
                docstring = docstring.split('\n')
                short_string = docstring[0].strip()
                if short_string == '':
                    short_string = docstring[1].strip()
            print("{0}: {1}".format(method, short_string))

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
        except NoResultFound, e:
            raise ValueError('Could not find metadata record for: {0}'.format(identifier))
        except MultipleResultsFound, e:
            raise e

        return record

    def __get_measurand(self, measurand):
        session = Session()
        query = session.query(Measurand).filter(Measurand.short_id == measurand)
        try:
            record = query.one()
        except NoResultFound, e:
            raise ValueError('Could not find measurand ({0}) in the database.'.format(measurand))
        except MultipleResultsFound, e:
            raise e

        return record


    def __get_tsdb_file_by_id(self, identifier, measurand, ftype='tsdb'):
        record = self.__get_record_by_id(identifier)
        measurand = self.__get_measurand(measurand)
        return os.path.join(self.__data_dir(), record.timeseries_id +
                '_' + measurand.long_id +
                '.' + ftype
                )

    def bulk_write(self, identifier, measurand, ts):
        writer.bulk_write(self.__get_tsdb_file_by_id(identifier, measurand), ts)

    def write(self, identifier, measurand, ts):
        modified = writer.write(self.__get_tsdb_file_by_id(identifier, measurand), ts)

        log_file = self.__get_tsdb_file_by_id(identifier, measurand, 'hdf5')

        writer.write_log(log_file, modified, datetime.utcnow())

    def read_all(self, identifier, measurand):
        return reader.read_all(self.__get_tsdb_file_by_id(identifier, measurand))

    def list(self):
        """
            Returns list of primary ID for all timeseries records.
        """
        session = Session()
        records = session.query(Timeseries).all()
        return [ record.primary_id for record in records ]

    def __str__(self):
        return self.tsdb_path
