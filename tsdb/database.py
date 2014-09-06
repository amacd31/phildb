from datetime import datetime
import hashlib
import os
import types
import uuid

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
from .exceptions import DuplicateError, MissingAttributeError, MissingDataError

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
        """
            Returns the version number of the database schema.

            :returns: string -- Schema version.
        """
        session = Session()
        query = session.query(SchemaVersion.version)

        version = query.scalar()

        return version

    def add_timeseries(self, identifier):
        """
            Create a timeseries entry to be identified by the supplied ID.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
        """
        the_id = identifier.strip()
        session = Session()
        ts = Timeseries(primary_id = identifier)
        session.add(ts)
        session.commit()

    def add_measurand(self, measurand_short_id, measurand_long_id, description):
        """
            Create a measurand entry.

            Measurand being a measurable timeseries type. e.g. Streamflow, Temperature, Rainfall, etc.

            :param measurand_short_id: Short identifier of the measurand.
            :type measurand_short_id: string
            :param measurand_long_id: Long identifier of the measurand.
            :type measurand_long_id: string
            :param description: Description of the measurand.
            :type description: string
        """
        short_id = measurand_short_id.strip()
        long_id = measurand_long_id.strip()
        session = Session()
        measurand = Measurand(short_id = short_id, long_id = long_id,  description = description)
        session.add(measurand)
        session.commit()

    def add_source(self, source, description):
        """
            Define a source.

            Source being the origin of the data. For example the source used in
            the examples/hrs example is BOM_HRS. Indicated the origin of the
            data was the Bureau of Metorology Hydrologic Reference Stations
            project.

            :param source: Identifier of the source.
            :type source: string
            :param description: Description of the source.
            :type description: string
        """
        short_id = source.strip().upper()
        session = Session()
        source = Source(short_id = short_id, description = description)
        session.add(source)
        session.commit()


    def __parse_attribute_kwargs(self, **kwargs):
        """
            Convert kwargs of attribute short IDs into database objects

            :param **kwargs: Any additional attributes to attach to the timeseries instance.
            :type **kwargs: kwargs

            :return: Dictionary of attributes from the database.
        """
        session = kwargs.pop('session', None)
        attributes = {}
        for attribute, value in kwargs.items():
            attributes[attribute] = self.__get_attribute(attribute, value, session)

        return attributes

    def add_timeseries_instance(self, identifier, freq, initial_metadata, **kwargs):
        """
            Define an instance of a timeseries.

            A timeseries instance is a combination of a timeseries, frequency and attributes.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Data frequency (e.g. 'D' for day, as supported by pandas.)
            :type freq: string
            :param initial_metadata: Store some metadata about this series.
                Potentially freeform header from a source file about to be loaded.
            :type initial_metadata: string
            :param **kwargs: Any additional attributes to attach to the timeseries instance.
            :type **kwargs: kwargs
        """
        session = Session()

        timeseries = self.__get_record_by_id(identifier, session)

        attributes = self.__parse_attribute_kwargs(session = session, **kwargs)

        query = session.query(TimeseriesInstance). \
                filter_by(timeseries=timeseries, freq=freq, **attributes)
        try:
            record = query.one()
            session.rollback()
            raise DuplicateError('TimeseriesInstance for ({:}) already exists.'. \
                    format(identifier, **kwargs))
        except NoResultFound as e:
            # No result is good, we can now create a ts instance.
            pass

        with session.no_autoflush:
            tsi = TimeseriesInstance(initial_metadata = initial_metadata)
            tsi.measurand = attributes['measurand']
            tsi.source = attributes['source']
            tsi.freq = freq
            tsi.uuid = uuid.uuid4().hex
            timeseries.ts_instances.append(tsi)

            session.add(tsi)
            session.commit()

    def __get_record_by_id(self, identifier, session = None):
        """
            Get a database record for the given timeseries ID.

            If a timeseries record can not be found a MissingDataError is raised.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param session: Database session to use. (Optional)
            :type session: sqlalchemy.orm.sessionmaker.Session
            :returns: Single session.query result.
            :raises: MissingDataError
        """
        if session is None:
            session = Session()

        query = session.query(Timeseries).filter(Timeseries.primary_id == identifier)
        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingDataError('Could not find metadata record for: {0}'.format(identifier))

        return record


    def __get_attribute(self, attribute, value, session = None):
        """
            Get a database record for the given attribute.

            If a attribute record can not be found a MissingAttributeError is raised.

            :param attribute: Identifier of the attribute.
            :type attribute: string
            :param session: Database session to use. (Optional)
            :type session: sqlalchemy.orm.sessionmaker.Session
            :returns: Single session.query result.
            :raises: MissingAttributeError
        """
        if session is None:
            session = Session()

        if attribute == 'measurand':
            query = session.query(Measurand).filter(Measurand.short_id == value)
        elif attribute == 'source':
            query = session.query(Source).filter(Source.short_id == value)
        else:
            raise MissingAttributeError('Attribute {0} unknown'.format(attribute))

        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingAttributeError('Could not find {0} ({1}) in the database.'.format(attribute, value))

        return record


    def __get_tsdb_file_by_id(self, identifier, freq, ftype='tsdb', **kwargs):
        """
            Get a path to a file for a given timeseries instance.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param ftype: File extension to use (i.e. the type of file).
                (Default='tsdb')
            :type ftype: string
            :returns: string -- Path to file for a timeseries instance identified
                by the given arguments.
        """
        record = self.__get_ts_instance(identifier, freq, **kwargs)

        return os.path.join(self.__data_dir(), record.uuid +
                '.' + ftype
                )


    def write(self, identifier, freq, ts, **kwargs):
        """
            Write/update timeseries data for existing timeseries.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Data frequency (e.g. 'D' for day, as supported by pandas.)
            :type freq: string
            :param ts: Timeseries data to write into the database.
            :type ts: np.array([np.array(datetime.date), np.array(float)])
        """
        modified = writer.write(self.__get_tsdb_file_by_id(identifier, freq, **kwargs), ts, freq)

        log_file = self.__get_tsdb_file_by_id(identifier, freq, ftype = 'hdf5', **kwargs)

        writer.write_log(log_file, modified, datetime.utcnow())

    def read_all(self, identifier, freq, **kwargs):
        """
            Read the entire timeseries record for the requested timeseries instance.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Timeseries data frequency.
            :type freq: string
            :returns: pandas.DataFrame -- Timeseries data.
        """
        return reader.read_all(self.__get_tsdb_file_by_id(identifier, freq, **kwargs))

    def ts_list(self, **kwargs):
        """
            Returns list of primary ID for all timeseries records.

            :param kwargs: Restrict to records associated with this the kwargs
                attributes supplied. (Optional).
            :type kwargs: kwargs
            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = Session()
        query_args = self.__parse_attribute_kwargs(**kwargs)

        records = session.query(TimeseriesInstance).filter_by(**query_args)
        return sorted(list(set([ record.timeseries.primary_id for record in records ])))

    def list_ids(self):
        """
            Returns list of timeseries IDs for all timeseries records.

            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = Session()

        records = session.query(Timeseries)
        return sorted(list(set([ record.primary_id for record in records ])))

    def list_measurands(self):
        """
            Returns list of measurand short IDs for all measurand records.

            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = Session()

        records = session.query(Measurand)
        return sorted(list(set([ record.short_id for record in records ])))

    def read_metadata(self, ts_id, freq, **kwargs):
        """
            Returns the metadata that was associated with an initial TimeseriesInstance.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :returns: string -- The initial metadata that was recorded on
                instance creation.
        """
        return self.__get_ts_instance(ts_id, freq, **kwargs).initial_metadata

    def __get_ts_instance(self, ts_id, freq, **kwargs):
        """
            Get a database record for the requested timeseries instance.

            If a timeseries instance record can not be found a MissingDataError is
            raised.

            :param ts_id: Identifier of the timeseries.
            :type ts_id: string
            :returns: dbstructures.TimeseriesInstance -- Single session.query result.
            :raises: MissingDataError
        """
        timeseries = self.__get_record_by_id(ts_id)

        query_args = self.__parse_attribute_kwargs(**kwargs)

        session = Session()
        query = session.query(TimeseriesInstance). \
                filter_by(timeseries=timeseries, freq=freq, **query_args)

        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingDataError('Could not find TimeseriesInstance for ({:}).'. \
                    format(ts_id, freq, **kwargs))

        return record

    def __str__(self):
        return self.tsdb_path
