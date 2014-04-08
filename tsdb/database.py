from datetime import datetime
import hashlib
import os
import types

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
Session = sessionmaker()

import logging
logger = logging.getLogger('TSDB_database')

from . import constants
from . import reader
from . import writer
from .dbstructures import SchemaVersion, Timeseries, Measurand, TimeseriesInstance
from .dbstructures import Source

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

        version = query.scalar()

        return version

    def add_timeseries(self, identifier):
        the_id = identifier.strip()
        session = Session()
        ts = Timeseries(primary_id = identifier, timeseries_id = hashlib.md5(identifier.encode('utf-8')).hexdigest())
        session.add(ts)
        session.commit()

    def add_measurand(self, measurand_short_id, measurand_long_id, description):
        short_id = measurand_short_id.strip().upper()
        long_id = measurand_long_id.strip().upper()
        session = Session()
        measurand = Measurand(short_id = short_id, long_id = long_id,  description = description)
        session.add(measurand)
        session.commit()

    def add_source(self, source, description):
        short_id = source.strip().upper()
        session = Session()
        source = Source(short_id = short_id, description = description)
        session.add(source)
        session.commit()

    def add_timeseries_instance(self, identifier, measurand_id, source_id, initial_metadata):
        session = Session()

        timeseries = self.__get_record_by_id(identifier, session)
        measurand = self.__get_measurand(measurand_id, session)
        source = self.__get_source(source_id, session)

        query = session.query(TimeseriesInstance). \
                filter_by(measurand = measurand, timeseries=timeseries, source=source)
        try:
            record = query.one()
            session.rollback()
            raise ValueError('TimeseriesInstance for ({0}, {1}, {2}) already exists.'. \
                    format(identifier, source_id, measurand_id))
        except NoResultFound as e:
            # No result is good, we can now create a ts instance.
            pass

        with session.no_autoflush:
            tsi = TimeseriesInstance(initial_metadata = initial_metadata)
            tsi.measurand = measurand
            tsi.source = source
            timeseries.ts_instances.append(tsi)

            session.add(tsi)
            session.commit()

    def __get_record_by_id(self, identifier, session = None):
        if session is None:
            session = Session()

        query = session.query(Timeseries).filter(Timeseries.primary_id == identifier)
        try:
            record = query.one()
        except NoResultFound as e:
            raise ValueError('Could not find metadata record for: {0}'.format(identifier))

        return record

    def __get_measurand(self, measurand, session = None):
        if session is None:
            session = Session()

        query = session.query(Measurand).filter(Measurand.short_id == measurand)
        try:
            record = query.one()
        except NoResultFound as e:
            raise ValueError('Could not find measurand ({0}) in the database.'.format(measurand))

        return record

    def __get_source(self, source_id, session = None):
        if session is None:
            session = Session()

        query = session.query(Source).filter(Source.short_id == source_id)
        try:
            record = query.one()
        except NoResultFound as e:
            raise ValueError('Could not find source ({0}) in the database.'.format(source_id))

        return record

    def __get_tsdb_file_by_id(self, identifier, measurand_id, source_id, ftype='tsdb'):
        record = self.__get_ts_instance(identifier, measurand_id, source_id)

        return os.path.join(self.__data_dir(), record.timeseries.timeseries_id +
                '_' + record.measurand.long_id +
                '_' + record.source.short_id +
                '.' + ftype
                )

    def bulk_write(self, identifier, measurand, ts, source):
        writer.bulk_write(self.__get_tsdb_file_by_id(identifier, measurand, source), ts)

    def write(self, identifier, measurand, ts, source):
        modified = writer.write(self.__get_tsdb_file_by_id(identifier, measurand, source), ts)

        log_file = self.__get_tsdb_file_by_id(identifier, measurand, source, 'hdf5')

        writer.write_log(log_file, modified, datetime.utcnow())

    def read_all(self, identifier, measurand, source):
        return reader.read_all(self.__get_tsdb_file_by_id(identifier, measurand, source))

    def ts_list(self, measurand_id = None, source_id = None):
        """
            Returns list of primary ID for all timeseries records.
        """
        session = Session()

        query_args = {}
        if measurand_id:
            query_args['measurand'] = self.__get_measurand(measurand_id)
        if source_id:
            query_args['source'] = self.__get_source(source_id)

        records = session.query(TimeseriesInstance).filter_by(**query_args)
        return [ record.timeseries.primary_id for record in records ]

    def read_metadata(self, ts_id, measurand_id, source_id):
        """
            Returns the metadata that was associated with an initial TimeseriesInstance.
        """
        return self.__get_ts_instance(ts_id, measurand_id, source_id).initial_metadata

    def __get_ts_instance(self, ts_id, measurand_id, source_id):
        timeseries = self.__get_record_by_id(ts_id)
        measurand = self.__get_measurand(measurand_id)
        source = self.__get_source(source_id)
        session = Session()
        query = session.query(TimeseriesInstance). \
                filter_by(measurand = measurand, timeseries=timeseries, source=source)

        try:
            record = query.one()
        except NoResultFound as e:
            raise ValueError('Could not find TimeseriesInstance for ({0}, {1}, {2}).'. \
                    format(ts_id, source_id, measurand_id))

        return record

    def __str__(self):
        return self.tsdb_path
