from datetime import datetime
import hashlib
import os
import types
import uuid

import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.orm.exc import NoResultFound

import logging

logger = logging.getLogger("PhilDB_database")

from phildb import constants
from phildb import reader
from phildb import writer
from phildb.dbstructures import SchemaVersion, Timeseries, Measurand, TimeseriesInstance
from phildb.dbstructures import Source
from phildb.dbstructures import Attribute, AttributeValue
from phildb.exceptions import DuplicateError, MissingAttributeError, MissingDataError


class PhilDB(object):
    def __init__(self, tsdb_path):
        self.tsdb_path = tsdb_path

        logger.debug(self.__meta_data_db())

        if not os.path.exists(self.tsdb_path):
            raise IOError("PhilDB database doesn't exist ({0})".format(self.tsdb_path))

        if not os.path.exists(self.__meta_data_db()):
            raise IOError(
                "PhilDB database doesn't contain meta-database ({0})".format(
                    self.__meta_data_db()
                )
            )

        self.__engine = create_engine("sqlite:///{0}".format(self.__meta_data_db()))
        self.Session = sessionmaker()
        self.Session.configure(bind=self.__engine)

        assert self.version() == constants.DB_VERSION

    def __meta_data_db(self):
        return os.path.join(self.tsdb_path, constants.METADATA_DB)

    def __data_dir(self):
        return os.path.join(self.tsdb_path, "data")

    def help(self):
        """
            List methods of the PhilDB class with the first line of their docstring.
        """
        for method in sorted(dir(self)):
            if method.startswith("_"):
                continue
            if not isinstance(getattr(self, method), types.MethodType):
                continue

            docstring = getattr(self, method).__doc__
            if docstring is None:
                short_string = ""
            else:
                docstring = docstring.split("\n")
                short_string = docstring[0].strip()
                if short_string == "":
                    short_string = docstring[1].strip()
            print("{0}: {1}".format(method, short_string))

    def version(self):
        """
            Returns the version number of the database schema.

            :returns: string -- Schema version.
        """
        session = self.Session()
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
        session = self.Session()
        ts = Timeseries(primary_id=the_id)
        session.add(ts)
        try:
            session.commit()
        except IntegrityError:
            raise DuplicateError("Already exists: '{0}'".format(the_id))

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
        session = self.Session()
        measurand = Measurand(
            short_id=short_id, long_id=long_id, description=description
        )
        session.add(measurand)
        try:
            session.commit()
        except IntegrityError:
            raise DuplicateError("Already exists: '{0}'".format(measurand_short_id))

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
        short_id = source.strip()
        session = self.Session()
        source = Source(short_id=short_id, description=description)
        session.add(source)
        try:
            session.commit()
        except IntegrityError:
            raise DuplicateError("Already exists: '{0}'".format(source))

    def add_attribute(self, attribute_id, description):
        """
            Define an attribute.

            :param attribute_id: Identifier of the attribute.
            :type attribute_id: string
            :param description: Description of the attribute.
            :type description: string
        """
        short_id = attribute_id.strip().upper()
        session = self.Session()
        attribute = Attribute(short_id=short_id, description=description)
        session.add(attribute)
        session.commit()

    def add_attribute_value(self, attribute_id, value):
        """
            Store an attribute value.

            :param attribute_id: Identifier of the attribute.
            :type attribute_id: string
            :param value: The attribute value to store.
            :type value: string
        """
        short_id = attribute_id.strip().upper()
        session = self.Session()

        query = session.query(Attribute).filter(Attribute.short_id == short_id)
        try:
            attribute = query.one()
        except NoResultFound as e:
            raise MissingAttributeError(
                "Could not find {0} ({1}) in the database.".format(attribute_id, value)
            )

        attribute = AttributeValue(attribute_id=attribute.id, attribute_value=value)
        session.add(attribute)
        session.commit()

    def __parse_attribute_kwargs(self, **kwargs):
        """
            Convert kwargs of attribute short IDs into database objects

            :param **kwargs: Any additional attributes to attach to the timeseries instance.
            :type \*\*kwargs: kwargs

            :return: Dictionary of attributes from the database.
        """
        session = kwargs.pop("session", None)
        attributes = {}
        for attribute, value in kwargs.items():
            if value is None:
                continue
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
            :param \*\*kwargs: Any additional attributes to attach to the timeseries instance.
            :type \*\*kwargs: kwargs
        """
        session = self.Session()

        timeseries = self.__get_record_by_id(identifier, session)

        attributes = self.__parse_attribute_kwargs(session=session, **kwargs)

        query = session.query(TimeseriesInstance).filter_by(
            timeseries=timeseries, freq=freq, **attributes
        )
        try:
            record = query.one()
            session.rollback()
            raise DuplicateError(
                "TimeseriesInstance for ({:}) already exists.".format(
                    identifier, **kwargs
                )
            )
        except NoResultFound as e:
            # No result is good, we can now create a ts instance.
            pass

        with session.no_autoflush:
            tsi = TimeseriesInstance(initial_metadata=initial_metadata)
            tsi.measurand = attributes["measurand"]
            tsi.source = attributes["source"]
            tsi.freq = freq
            tsi.uuid = uuid.uuid4().hex
            timeseries.ts_instances.append(tsi)

            session.add(tsi)
            try:
                session.commit()
            except IntegrityError:
                raise DuplicateError(
                    "Timeseries instance already exists: '{0}', '{1}'".format(
                        identifier, freq
                    )
                )

    def __get_record_by_id(self, identifier, session=None):
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
            session = self.Session()

        query = session.query(Timeseries).filter(Timeseries.primary_id == identifier)
        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingDataError(
                "Could not find metadata record for: {0}".format(identifier)
            )

        return record

    def __get_attribute(self, attribute, value, session=None):
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
            session = self.Session()

        if attribute == "measurand":
            query = session.query(Measurand).filter(Measurand.short_id == value)
        elif attribute == "source":
            query = session.query(Source).filter(Source.short_id == value)
        elif attribute == "timeseries":
            query = session.query(Timeseries).filter(Timeseries.primary_id == value)
        elif attribute == "provider":
            short_id = attribute.strip().upper()
            query = session.query(Attribute).filter(Attribute.short_id == short_id)
            try:
                record = query.one()
            except NoResultFound as e:
                raise MissingAttributeError(
                    "Could not find {0} ({1}) in the database.".format(attribute, value)
                )
            query = session.query(AttributeValue).filter(
                AttributeValue.attribute_id == record.id,
                AttributeValue.attribute_value == value,
            )
        else:
            raise MissingAttributeError("Attribute {0} unknown".format(attribute))

        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingAttributeError(
                "Could not find {0} ({1}) in the database.".format(attribute, value)
            )

        return record

    def get_file_path(self, identifier, freq, ftype="tsdb", **kwargs):
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

        return os.path.join(self.__data_dir(), record.uuid + "." + ftype)

    def write(self, identifier, freq, ts, **kwargs):
        """
            Write/update timeseries data for existing timeseries.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Data frequency (e.g. 'D' for day, as supported by pandas.)
            :type freq: string
            :param ts: Timeseries data to write into the database.
            :type ts: pd.Series
        """
        modified = writer.write(
            self.get_file_path(identifier, freq, **kwargs), ts, freq
        )

        log_file = self.get_file_path(identifier, freq, ftype="hdf5", **kwargs)

        writer.write_log(log_file, modified, datetime.utcnow())

    def read(self, identifier, freq, **kwargs):
        """
            Read the entire timeseries record for the requested timeseries instance.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Timeseries data frequency.
            :type freq: string
            :param kwargs: Attributes to match against timeseries instances (e.g. source, measurand).
            :type kwargs: kwargs

            :returns: pandas.DataFrame -- Timeseries data.
        """
        return reader.read(self.get_file_path(identifier, freq, **kwargs))

    def read_log(self, identifier, freq, as_at_datetime, **kwargs):
        """
            Read timeseries record for the requested timeseries instance as it was at specified datetime in the log.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Timeseries data frequency.
            :type freq: string
            :param as_at_datetime: Filter to a timeseries, as available at this specified datetime, from the log.
            :type as_at_datetime: datetime
            :param kwargs: Attributes to match against timeseries instances (e.g. source, measurand).
            :type kwargs: kwargs

            :returns: pandas.DataFrame -- Timeseries data.
        """
        return reader.read_log(
            self.get_file_path(identifier, freq, ftype="hdf5", **kwargs), as_at_datetime
        )

    def read_all(self, freq, excludes=None, **kwargs):
        """
            Read the entire timeseries record for all matching timeseries instances.
            Optionally exclude timeseries from the final DataFrame by specifying IDs in the exclude argument.

            :param identifier: Identifier of the timeseries.
            :type identifier: string
            :param freq: Timeseries data frequency.
            :type freq: string
            :param excludes: IDs of timeseries to exclude from final DataFrame.
            :type excludes: array[string]
            :param kwargs: Attributes to match against timeseries instances (e.g. source, measurand).
            :type kwargs: kwargs

            :returns: pandas.DataFrame -- Timeseries data.
        """
        data = {}
        if excludes is None:
            identifiers = self.ts_list(**kwargs)
        else:
            identifiers = set(self.ts_list(**kwargs)).difference(excludes)

        return self.read_dataframe(identifiers, freq, **kwargs)

    def read_dataframe(self, identifiers, freq, **kwargs):
        """
            Read the entire timeseries record for the requested timeseries instances.

            :param identifiers: Identifiers of the timeseries to read into a DataFrame.
            :type identifiers: array[string]
            :param freq: Timeseries data frequency.
            :type freq: string
            :param kwargs: Attributes to match against timeseries instances (e.g. source, measurand).
            :type kwargs: kwargs

            :returns: pandas.DataFrame -- Timeseries data.
        """
        data = {}
        for ts_id in identifiers:
            data[ts_id] = reader.read(self.get_file_path(ts_id, freq, **kwargs))
        return pd.DataFrame(data)

    def ts_list(self, **kwargs):
        """
            Returns list of primary ID for all timeseries records.

            :param kwargs: Restrict to records associated with this the kwargs
                attributes supplied. (Optional).
            :type kwargs: kwargs
            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = self.Session()
        query_args = self.__parse_attribute_kwargs(**kwargs)

        records = (
            session.query(TimeseriesInstance)
            .options(joinedload(TimeseriesInstance.timeseries))
            .filter_by(**query_args)
        )
        return sorted(list(set([record.timeseries.primary_id for record in records])))

    def list_ids(self):
        """
            Returns list of timeseries IDs for all timeseries records.

            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = self.Session()

        records = session.query(Timeseries)
        return sorted(list(set([record.primary_id for record in records])))

    def list_timeseries_instances(self, **kwargs):
        """
            Returns list of timeseries instances for all instance records.

            Can filter by using keyword arguments.

            :returns: list(string) -- Sorted list of timeseries instances.
        """
        session = self.Session()

        initial_args = {}
        for attr in ["freq"]:
            attr_val = kwargs.pop(attr, None)

            if attr_val:
                initial_args[attr] = attr_val

        query_args = self.__parse_attribute_kwargs(**kwargs)
        query_args.update(initial_args)

        records = (
            session.query(TimeseriesInstance)
            .options(joinedload(TimeseriesInstance.timeseries))
            .filter_by(**query_args)
        )
        instance_list = []
        for record in records:
            instance = {
                "ts_id": record.timeseries.primary_id,
                "freq": record.freq,
                "measurand": record.measurand.short_id,
                "source": record.source.short_id,
            }
            instance_list.append(instance)

        return pd.DataFrame(instance_list)

    def list_measurands(self):
        """
            Returns list of measurand short IDs for all measurand records.

            :returns: list(string) -- Sorted list of timeseries identifiers.
        """
        session = self.Session()

        records = session.query(Measurand)
        return sorted(list(set([record.short_id for record in records])))

    def list_sources(self):
        """
            Returns list of source IDs for all sources.

            :returns: list(string) -- Sorted list of source identifiers.
        """
        session = self.Session()

        records = session.query(Source)
        return sorted(list(set([record.short_id for record in records])))

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

        session = self.Session()
        query = session.query(TimeseriesInstance).filter_by(
            timeseries=timeseries, freq=freq, **query_args
        )

        try:
            record = query.one()
        except NoResultFound as e:
            raise MissingDataError(
                "Could not find TimeseriesInstance for ({:}).".format(
                    ts_id, freq, **kwargs
                )
            )

        return record

    def __str__(self):
        return self.tsdb_path
