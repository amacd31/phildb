from datetime import datetime
import gc
import itertools
import mock
import os
import pandas as pd
import shutil
import sqlite3
import tables
import tempfile
import unittest
import uuid

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound

Session = sessionmaker()

from phildb.database import PhilDB
from phildb.dbstructures import TimeseriesInstance
from phildb.create import create
from phildb.exceptions import DuplicateError, MissingAttributeError, MissingDataError

uuid_pool = itertools.cycle(["47e4e0b4-0c04-4c1d-8dc4-272acfcd6bb3"])


def generate_uuid():
    return uuid.UUID(next(uuid_pool))


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.temp_dir = tempfile.mkdtemp()

        self.test_tsdb = os.path.join(tempfile.mkdtemp(), "tsdb")
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), "test_data", "test_tsdb"),
            self.test_tsdb,
        )

        self.second_test_db = os.path.join(tempfile.mkdtemp(), "second_db")
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), "test_data", "second_test_tsdb"),
            self.second_test_db,
        )

        db_name = os.path.join(self.test_data_dir, self.test_tsdb)
        self.db = PhilDB(self.test_tsdb)

    def tearDown(self):
        # On Windows files can't be removed while still open.
        # The time between the db object going out of scope and tear down
        # occurring is too short for garbage collection to have run.
        # As a result SQLAlchemy has not released the sqlite file by the
        # time tear down occurs.
        # This results in an error on Windows:
        #     PermissionError: [WinError 32] The process cannot access the file
        #     because it is being used by another process:
        # Therefore garbage collect before trying to remove temporary files.
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir)
        except OSError as e:
            if e.errno != 2:  # Code 2: No such file or directory.
                raise

        try:
            shutil.rmtree(self.test_tsdb)
        except OSError as e:
            if e.errno != 2:  # Code 2: No such file or directory.
                raise

        try:
            shutil.rmtree(self.second_test_db)
        except OSError as e:
            if e.errno != 2:  # Code 2: No such file or directory.
                raise

    def test_tsdb_exists(self):
        db_name = os.path.join(self.test_data_dir, "this_tsdb_does_not_exist")
        with self.assertRaises(IOError) as context:
            db = PhilDB(db_name)

        self.assertEqual(
            str(context.exception),
            "PhilDB database doesn't exist ({0})".format(db_name),
        )

    def test_missing_meta_data(self):
        db_name = os.path.join(self.test_data_dir, "missing_meta_data")
        with self.assertRaises(IOError) as context:
            db = PhilDB(db_name)

        self.assertEqual(
            str(context.exception),
            "PhilDB database doesn't contain meta-database ({0}{1}{2})".format(
                db_name, os.path.sep, "tsdb.sqlite"
            ),
        )

    def test_meta_data(self):
        db_name = os.path.join(self.test_data_dir, "test_tsdb")
        db = PhilDB(db_name)

        self.assertEqual(db.version(), "0.0.6")

    def test_tsdb_data_dir(self):
        db_name = os.path.join(self.test_data_dir, "test_tsdb")
        db = PhilDB(db_name)
        self.assertEqual(db._PhilDB__data_dir(), os.path.join(db_name, "data"))

    @mock.patch("uuid.uuid4", generate_uuid)
    def test_tsdb_get_file_path(self):

        self.db.add_timeseries("xyz")
        self.db.add_timeseries_instance(
            "xyz", "D", "xyz", measurand="Q", source="DATA_SOURCE"
        )
        self.assertEqual(
            self.db.get_file_path("xyz", "D"),
            os.path.join(
                self.test_tsdb, "data", "47e4e0b40c044c1d8dc4272acfcd6bb3.tsdb"
            ),
        )

        self.assertEqual(
            self.db.get_file_path("xyz", "D", ftype="hdf5"),
            os.path.join(
                self.test_tsdb, "data", "47e4e0b40c044c1d8dc4272acfcd6bb3.hdf5"
            ),
        )

    def test_add_ts_entry(self):
        create(self.temp_dir)
        db = PhilDB(self.temp_dir)
        db.add_timeseries("410730")

        conn = sqlite3.connect(db._PhilDB__meta_data_db())
        c = conn.cursor()
        c.execute("SELECT * FROM timeseries;")
        pk, primary_id = c.fetchone()

        self.assertEqual(primary_id, "410730")

    def test_add_measurand_entry(self):
        create(self.temp_dir)
        db = PhilDB(self.temp_dir)
        db.add_measurand("P", "PRECIPITATION", "Precipitation")

        conn = sqlite3.connect(db._PhilDB__meta_data_db())
        c = conn.cursor()
        c.execute("SELECT * FROM measurand;")
        pk, measurand_short_id, measurand_long_id, measurand_description = c.fetchone()

        self.assertEqual(measurand_short_id, "P")
        self.assertEqual(measurand_long_id, "PRECIPITATION")
        self.assertEqual(measurand_description, "Precipitation")

    def test_read(self):
        db_name = os.path.join(self.test_data_dir, "test_tsdb")
        db = PhilDB(db_name)

        results = db.read("410730", "D", measurand="Q", source="DATA_SOURCE")

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.values[0], 1)
        self.assertEqual(results.values[1], 2)
        self.assertEqual(results.values[2], 3)

    def test_read_unique(self):
        db = PhilDB(self.test_tsdb)

        results = db.read("410730", "D")
        self.assertEqual(results.values[0], 1)
        self.assertEqual(results.values[1], 2)
        self.assertEqual(results.values[2], 3)

    def test_read_non_unique(self):
        db = PhilDB(self.test_tsdb)

        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        db.add_timeseries_instance(
            "410730", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )

        with self.assertRaises(MultipleResultsFound) as context:
            results = db.read("410730", "D")

    @mock.patch("uuid.uuid4", generate_uuid)
    def test_new_write(self):
        db = PhilDB(self.test_tsdb)

        db.add_timeseries("410731")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="DATA_SOURCE"
        )
        db.write(
            "410731",
            "D",
            pd.Series(
                index=[
                    datetime(2014, 1, 1),
                    datetime(2014, 1, 2),
                    datetime(2014, 1, 3),
                ],
                data=[1.0, 2.0, 3.0],
            ),
            measurand="Q",
            source="DATA_SOURCE",
        )

        results = db.read("410731", "D", measurand="Q", source="DATA_SOURCE")

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.values[0], 1.0)
        self.assertEqual(results.values[1], 2.0)
        self.assertEqual(results.values[2], 3.0)

    def test_update_and_append(self):
        db = PhilDB(self.test_tsdb)
        db.write(
            "410730",
            "D",
            pd.Series(
                index=[
                    datetime(2014, 1, 2),
                    datetime(2014, 1, 3),
                    datetime(2014, 1, 4),
                    datetime(2014, 1, 5),
                    datetime(2014, 1, 6),
                ],
                data=[2.5, 3.0, 4.0, 5.0, 6.0],
            ),
            measurand="Q",
            source="DATA_SOURCE",
        )

        data = db.read("410730", "D", measurand="Q", source="DATA_SOURCE")
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.5, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertEqual(5.0, data.values[4])
        self.assertEqual(6.0, data.values[5])
        self.assertEqual(datetime(2014, 1, 1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014, 1, 2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014, 1, 3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014, 1, 4), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014, 1, 5), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014, 1, 6), data.index[5].to_pydatetime())

    def test_write_non_existant_id(self):
        db = PhilDB(self.test_tsdb)
        self.assertRaises(
            MissingDataError,
            db.write,
            "DOESNOTEXIST",
            "D",
            [[datetime(2014, 1, 1), datetime(2014, 1, 2)], [2.0, 3.0]],
            measurand="Q",
            source="DATA_SOURCE",
        )

    def test_write_non_existant_measurand(self):
        db = PhilDB(self.test_tsdb)
        self.assertRaises(
            MissingAttributeError,
            db.write,
            "410730",
            "D",
            [[datetime(2014, 1, 1), datetime(2014, 1, 2)], [2.0, 3.0]],
            measurand="DOESNOTEXIST",
            source="DATA_SOURCE",
        )

    def test_ts_list(self):
        db = PhilDB(self.test_tsdb)
        ts_list = db.ts_list()
        self.assertEqual(["123456", "410730"], ts_list)

    def test_ts_list_source(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_source("EXAMPLE_SOURCE", "Example source, i.e. a dataset")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="EXAMPLE_SOURCE"
        )

        ts_list = db.ts_list(source="EXAMPLE_SOURCE")
        self.assertEqual(["410731"], ts_list)

    def test_ts_list_measurand(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )

        ts_list = db.ts_list(measurand="P")
        self.assertEqual(["410731"], ts_list)

    def test_ts_list_ids(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )

        ts_list = db.list_ids()
        self.assertEqual(["123456", "410730", "410731"], ts_list)

    def test_ts_list_unique_ids(self):
        """
            Test that IDs don't appear multiple times due to different combinations.
        """
        db = PhilDB(self.test_tsdb)
        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        db.add_timeseries_instance(
            "410730", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )

        ts_list = db.ts_list()
        self.assertEqual(["123456", "410730"], ts_list)

    def test_ts_list_sorted(self):
        """
            Test that the list of IDs is sorted.
        """
        db = PhilDB(self.test_tsdb)
        db.add_measurand("P", "PRECIPITATION", "Precipitation")

        db.add_timeseries_instance(
            "410730", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )

        db.add_timeseries("410731")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="P", source="DATA_SOURCE"
        )
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="DATA_SOURCE"
        )

        ts_list = db.ts_list()
        self.assertEqual(["123456", "410730", "410731"], ts_list)

    def test_measurand_list_sorted(self):
        """
            Test that the list of measurand short IDs is sorted.
        """
        db = PhilDB(self.test_tsdb)
        db.add_measurand("P", "PRECIPITATION", "Precipitation")

        ts_list = db.list_measurands()
        self.assertEqual(["P", "Q"], ts_list)

    def test_source_list_sorted(self):
        """
            Test that the list of source short IDs is sorted.
        """
        db = PhilDB(self.test_tsdb)
        db.add_source("EXAMPLE_SOURCE", "Example source.")

        ts_list = db.list_sources()
        self.assertEqual(["DATA_SOURCE", "EXAMPLE_SOURCE"], ts_list)

    def test_ts_list_measurand_and_source(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_source("EXAMPLE_SOURCE", "Example source, i.e. a dataset")
        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="P", source="EXAMPLE_SOURCE"
        )

        ts_list = db.ts_list(source="EXAMPLE_SOURCE", measurand="P")
        self.assertEqual(["410731"], ts_list)

    def test_duplicate_add_ts_instance(self):
        db = PhilDB(self.test_tsdb)
        self.assertRaises(
            DuplicateError,
            db.add_timeseries_instance,
            "410730",
            "D",
            "",
            measurand="Q",
            source="DATA_SOURCE",
        )

    def test_add_ts_instance(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="DATA_SOURCE"
        )

        Session.configure(bind=db._PhilDB__engine)
        session = Session()

        timeseries = db._PhilDB__get_record_by_id("410731", session)
        measurand = db._PhilDB__get_attribute("measurand", "Q", session)
        source = db._PhilDB__get_attribute("source", "DATA_SOURCE", session)

        query = session.query(TimeseriesInstance).filter_by(
            measurand=measurand, source=source, timeseries=timeseries
        )

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, "410731")
        self.assertEqual(record.measurand.short_id, "Q")
        self.assertEqual(record.source.short_id, "DATA_SOURCE")

    def test_add_ts_instance_alternate_freq(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries_instance(
            "410730", "M", "Foo", measurand="Q", source="DATA_SOURCE"
        )

        Session.configure(bind=db._PhilDB__engine)
        session = Session()

        timeseries = db._PhilDB__get_record_by_id("410730", session)
        measurand = db._PhilDB__get_attribute("measurand", "Q", session)
        source = db._PhilDB__get_attribute("source", "DATA_SOURCE", session)

        query = session.query(TimeseriesInstance).filter_by(
            measurand=measurand, source=source, timeseries=timeseries, freq="M"
        )

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, "410730")
        self.assertEqual(record.measurand.short_id, "Q")
        self.assertEqual(record.source.short_id, "DATA_SOURCE")
        self.assertEqual(record.freq, "M")

    def test_add_source(self):
        db = PhilDB(self.test_tsdb)
        db.add_source("EXAMPLE_SOURCE", "Example source, i.e. a dataset")
        db.add_timeseries_instance(
            "410730", "D", "Foo", measurand="Q", source="EXAMPLE_SOURCE"
        )

        Session.configure(bind=db._PhilDB__engine)
        session = Session()

        timeseries = db._PhilDB__get_record_by_id("410730", session)
        measurand = db._PhilDB__get_attribute("measurand", "Q", session)
        source = db._PhilDB__get_attribute("source", "EXAMPLE_SOURCE", session)

        query = session.query(TimeseriesInstance).filter_by(
            measurand=measurand, source=source, timeseries=timeseries
        )

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, "410730")
        self.assertEqual(record.measurand.short_id, "Q")
        self.assertEqual(record.source.short_id, "EXAMPLE_SOURCE")

    def test_add_attribute_with_value(self):
        db = PhilDB(self.test_tsdb)
        db.add_source("EXAMPLE_SOURCE", "Example source, i.e. a dataset")
        db.add_attribute("provider", "Data provider")
        db.add_attribute_value("provider", "EXAMPLE_PROVIDER")
        db.add_timeseries_instance(
            "410730", "D", "Foo", measurand="Q", source="EXAMPLE_SOURCE"
        )

        Session.configure(bind=db._PhilDB__engine)
        session = Session()

        timeseries = db._PhilDB__get_record_by_id("410730", session)
        measurand = db._PhilDB__get_attribute("measurand", "Q", session)
        source = db._PhilDB__get_attribute("source", "EXAMPLE_SOURCE", session)
        provider = db._PhilDB__get_attribute("provider", "EXAMPLE_PROVIDER", session)

        query = session.query(TimeseriesInstance).filter_by(
            measurand=measurand, source=source, timeseries=timeseries
        )

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, "410730")
        self.assertEqual(record.measurand.short_id, "Q")
        self.assertEqual(record.source.short_id, "EXAMPLE_SOURCE")

    def test_read_metadata(self):
        db = PhilDB(self.test_tsdb)
        db.add_timeseries("410731")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="DATA_SOURCE"
        )
        metadata = db.read_metadata("410730", "D", measurand="Q", source="DATA_SOURCE")
        self.assertEqual("", metadata)

        metadata = db.read_metadata("410731", "D", measurand="Q", source="DATA_SOURCE")
        self.assertEqual("Foo", metadata)

    def test_get_ts_instance(self):
        db = PhilDB(self.test_tsdb)
        ts_instance = db._PhilDB__get_ts_instance(
            "410730", "D", measurand="Q", source="DATA_SOURCE"
        )
        self.assertEqual("410730", ts_instance.timeseries.primary_id)
        self.assertEqual("Q", ts_instance.measurand.short_id)

        self.assertRaises(
            MissingDataError,
            db._PhilDB__get_ts_instance,
            "410731",
            "D",
            measurand="Q",
            source="DATA_SOURCE",
        )

        db.add_measurand("P", "PRECIPITATION", "Precipitation")
        self.assertRaises(
            MissingDataError,
            db._PhilDB__get_ts_instance,
            "410730",
            "D",
            measurand="P",
            source="DATA_SOURCE",
        )

    def test_read_all(self):
        db = PhilDB(self.test_tsdb)

        all = db.read_all("D", measurand="Q", source="DATA_SOURCE")
        self.assertEqual("123456", all.columns[0])
        self.assertEqual("410730", all.columns[1])

    def test_read_dataframe(self):
        db = PhilDB(self.test_tsdb)

        all = db.read_dataframe(
            ["410730", "123456"], "D", measurand="Q", source="DATA_SOURCE"
        )

        self.assertEqual(len(all.columns), 2)
        self.assertTrue("123456" in all.columns)
        self.assertTrue("410730" in all.columns)

    def test_read_all_with_exclusions(self):
        db = PhilDB(self.test_tsdb)

        all = db.read_all("D", excludes=["410730"], measurand="Q", source="DATA_SOURCE")
        self.assertEqual("123456", all.columns[0])

    def test_list_ts_instance(self):
        db = PhilDB(self.test_tsdb)

        results = db.list_timeseries_instances()
        self.assertEqual(len(results), 2)

        results = db.list_timeseries_instances(freq="D")
        self.assertEqual(len(results), 2)

        results = db.list_timeseries_instances(timeseries="410730")
        self.assertEqual(len(results), 1)
        self.assertEqual(results.loc[0]["ts_id"], "410730")
        self.assertEqual(results.loc[0]["measurand"], "Q")

    @mock.patch("uuid.uuid4", generate_uuid)
    def test_log_write(self):
        db = PhilDB(self.test_tsdb)

        db.add_timeseries("410731")
        db.add_timeseries_instance(
            "410731", "D", "Foo", measurand="Q", source="DATA_SOURCE"
        )
        dates = [datetime(2014, 1, 1), datetime(2014, 1, 2), datetime(2014, 1, 3)]
        db.write(
            "410731",
            "D",
            pd.Series(index=dates, data=[1.0, 2.0, 3.0]),
            measurand="Q",
            source="DATA_SOURCE",
        )

        db.write(
            "410731",
            "D",
            pd.Series(index=dates, data=[1.0, 2.5, 3.0]),
            measurand="Q",
            source="DATA_SOURCE",
        )

        db.write(
            "410731",
            "D",
            pd.Series(index=[datetime(2014, 1, 4)], data=[4.0]),
            measurand="Q",
            source="DATA_SOURCE",
        )

        results = db.read("410731", "D")
        self.assertEqual(results.values[0], 1.0)
        self.assertEqual(results.values[1], 2.5)
        self.assertEqual(results.values[2], 3.0)
        self.assertEqual(results.values[3], 4.0)

        with tables.open_file(
            db.get_file_path("410731", "D", ftype="hdf5"), "r"
        ) as hdf5_file:
            log_grp = hdf5_file.get_node("/data")

            self.assertEqual(log_grp.log[0][0], 1388534400)
            self.assertEqual(log_grp.log[0][1], 1.0)
            self.assertEqual(log_grp.log[0][2], 0)

            self.assertEqual(log_grp.log[1][0], 1388620800)
            self.assertEqual(log_grp.log[1][1], 2.0)

            self.assertEqual(log_grp.log[2][0], 1388707200)
            self.assertEqual(log_grp.log[2][1], 3.0)

            self.assertEqual(log_grp.log[3][0], 1388620800)
            self.assertEqual(log_grp.log[3][1], 2.5)

            self.assertEqual(log_grp.log[4][0], 1388793600)
            self.assertEqual(log_grp.log[4][1], 4.0)

    def test_add_duplicates(self):
        db = PhilDB(self.test_tsdb)
        with self.assertRaises(DuplicateError) as context:
            db.add_source("DATA_SOURCE", "Duplicate source")

        with self.assertRaises(DuplicateError) as context:
            db.add_measurand("Q", "STREAMFLOW", "Duplicate measurand")

        with self.assertRaises(DuplicateError) as context:
            db.add_timeseries("410730")

        with self.assertRaises(DuplicateError) as context:
            db.add_timeseries_instance(
                "410730", "D", "", source="DATA_SOURCE", measurand="Q"
            )

    def test_multiple_db_instances(self):
        db1 = PhilDB(self.test_tsdb)
        db2 = PhilDB(self.second_test_db)

        self.assertEqual(db1.list_measurands()[0], "Q")
        self.assertEqual(db2.list_measurands()[0], "2")
        self.assertEqual(db2.list_measurands()[1], "Q")
