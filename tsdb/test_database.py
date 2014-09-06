from datetime import datetime
import mock
import os
import shutil
import sqlite3
import tempfile
import unittest
import uuid

from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

from .database import TSDB
from .dbstructures import TimeseriesInstance
from .create import create
from .exceptions import DuplicateError, MissingAttributeError, MissingDataError

uuid_pool = iter(['47e4e0b4-0c04-4c1d-8dc4-272acfcd6bb3'])

def generate_uuid():
    return uuid.UUID(next(uuid_pool))

class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.temp_dir = tempfile.mkdtemp()

        self.test_tsdb = os.path.join(tempfile.mkdtemp(), 'tsdb')
        shutil.copytree(os.path.join(os.path.dirname(__file__),
            'test_data',
            'test_tsdb'),
            self.test_tsdb)

        db_name = os.path.join(self.test_data_dir, self.test_tsdb)
        db = TSDB(self.test_tsdb)

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

        try:
            shutil.rmtree(self.test_tsdb)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_tsdb_exists(self):
        db_name = os.path.join(self.test_data_dir, 'this_tsdb_does_not_exist')
        with self.assertRaises(IOError) as context:
            db = TSDB(db_name)

        self.assertEqual(str(context.exception),
            "TSDB doesn't exist ({0})".format(db_name))

    def test_missing_meta_data(self):
        db_name = os.path.join(self.test_data_dir, 'missing_meta_data')
        with self.assertRaises(IOError) as context:
            db = TSDB(db_name)

        self.assertEqual(str(context.exception),
            "TSDB doesn't contain meta-database ({0}{1}{2})".format(db_name, os.path.sep, 'tsdb.sqlite'))

    def test_meta_data(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        db = TSDB(db_name)

        self.assertEqual(db.version(), "0.0.5")

    def test_tsdb_data_dir(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        db = TSDB(db_name)
        self.assertEqual(db._TSDB__data_dir(), os.path.join(db_name, 'data'))

    def test_add_ts_entry(self):
        create(self.temp_dir)
        db = TSDB(self.temp_dir)
        db.add_timeseries('410730')

        conn = sqlite3.connect(db._TSDB__meta_data_db())
        c = conn.cursor()
        c.execute("SELECT * FROM timeseries;")
        pk, primary_id = c.fetchone();

        self.assertEqual(primary_id, '410730')

    def test_add_measurand_entry(self):
        create(self.temp_dir)
        db = TSDB(self.temp_dir)
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')

        conn = sqlite3.connect(db._TSDB__meta_data_db())
        c = conn.cursor()
        c.execute("SELECT * FROM measurand;")
        pk, measurand_short_id, measurand_long_id, measurand_description = c.fetchone();

        self.assertEqual(measurand_short_id, 'P')
        self.assertEqual(measurand_long_id, 'PRECIPITATION')
        self.assertEqual(measurand_description, 'Precipitation')

    def test_read_all(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        db = TSDB(db_name)

        results = db.read_all('410730', 'D', measurand = 'Q', source = 'DATA_SOURCE')

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.value[0], 1)
        self.assertEqual(results.value[1], 2)
        self.assertEqual(results.value[2], 3)

    @mock.patch('uuid.uuid4', generate_uuid)
    def test_new_write(self):
        db = TSDB(self.test_tsdb)

        db.add_timeseries('410731')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'Q', source = 'DATA_SOURCE')
        db.write('410731', 'D', [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, 2.0, 3.0]], measurand = 'Q', source = 'DATA_SOURCE')

        results = db.read_all('410731', 'D', measurand = 'Q', source = 'DATA_SOURCE')

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.value[0], 1.0)
        self.assertEqual(results.value[1], 2.0)
        self.assertEqual(results.value[2], 3.0)

    def test_update_and_append(self):
        db = TSDB(self.test_tsdb)
        db.write('410730', 'D', [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [2.5, 3.0, 4.0, 5.0, 6.0]], measurand = 'Q', source = 'DATA_SOURCE')

        data = db.read_all('410730', 'D', measurand = 'Q', source = 'DATA_SOURCE')
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.5, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertEqual(4.0, data.values[3][0])
        self.assertEqual(5.0, data.values[4][0])
        self.assertEqual(6.0, data.values[5][0])
        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014,1,4), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014,1,5), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014,1,6), data.index[5].to_pydatetime())

    def test_write_non_existant_id(self):
        db = TSDB(self.test_tsdb)
        self.assertRaises(MissingDataError, db.write, 'DOESNOTEXIST', 'D', [[datetime(2014,1,1), datetime(2014,1,2)], [2.0, 3.0]], measurand = 'Q', source = 'DATA_SOURCE')

    def test_write_non_existant_measurand(self):
        db = TSDB(self.test_tsdb)
        self.assertRaises(MissingAttributeError, db.write, '410730', 'D', [[datetime(2014,1,1), datetime(2014,1,2)], [2.0, 3.0]], measurand = 'DOESNOTEXIST', source = 'DATA_SOURCE')

    def test_ts_list(self):
        db = TSDB(self.test_tsdb)
        ts_list = db.ts_list()
        self.assertEqual(['410730'], ts_list)

    def test_ts_list_source(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_source('EXAMPLE_SOURCE', 'Example source, i.e. a dataset')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'Q', source = 'EXAMPLE_SOURCE')

        ts_list = db.ts_list(source = 'EXAMPLE_SOURCE')
        self.assertEqual(['410731'], ts_list)

    def test_ts_list_measurand(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'P', source = 'DATA_SOURCE')

        ts_list = db.ts_list(measurand = 'P')
        self.assertEqual(['410731'], ts_list)

    def test_ts_list_ids(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'P', source = 'DATA_SOURCE')

        ts_list = db.list_ids()
        self.assertEqual(['410730', '410731'], ts_list)

    def test_ts_list_unique_ids(self):
        """
            Test that IDs don't appear multiple times due to different combinations.
        """
        db = TSDB(self.test_tsdb)
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')
        db.add_timeseries_instance('410730', 'D', 'Foo', measurand = 'P', source = 'DATA_SOURCE')

        ts_list = db.ts_list()
        self.assertEqual(['410730'], ts_list)

    def test_ts_list_sorted(self):
        """
            Test that the list of IDs is sorted.
        """
        db = TSDB(self.test_tsdb)
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')

        db.add_timeseries_instance('410730', 'D', 'Foo', measurand = 'P', source = 'DATA_SOURCE')

        db.add_timeseries('410731')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'P', source = 'DATA_SOURCE')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'Q', source = 'DATA_SOURCE')

        ts_list = db.ts_list()
        self.assertEqual(['410730', '410731'], ts_list)

    def test_measurand_list_sorted(self):
        """
            Test that the list of measurand short IDs is sorted.
        """
        db = TSDB(self.test_tsdb)
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')

        ts_list = db.list_measurands()
        self.assertEqual(['P', 'Q'], ts_list)

    def test_ts_list_measurand_and_source(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_source('EXAMPLE_SOURCE', 'Example source, i.e. a dataset')
        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'P', source = 'EXAMPLE_SOURCE')

        ts_list = db.ts_list(source = 'EXAMPLE_SOURCE', measurand = 'P')
        self.assertEqual(['410731'], ts_list)

    def test_duplicate_add_ts_instance(self):
        db = TSDB(self.test_tsdb)
        self.assertRaises(DuplicateError, db.add_timeseries_instance, '410730', 'D', '', measurand = 'Q', source = 'DATA_SOURCE')

    def test_add_ts_instance(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'Q', source = 'DATA_SOURCE')

        Session.configure(bind=db._TSDB__engine)
        session = Session()

        timeseries = db._TSDB__get_record_by_id('410731', session)
        measurand = db._TSDB__get_attribute('measurand', 'Q', session)
        source = db._TSDB__get_attribute('source', 'DATA_SOURCE', session)

        query = session.query(TimeseriesInstance). \
                filter_by(measurand = measurand, source=source, timeseries=timeseries)

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, '410731')
        self.assertEqual(record.measurand.short_id, 'Q')
        self.assertEqual(record.source.short_id, 'DATA_SOURCE')

    def test_add_source(self):
        db = TSDB(self.test_tsdb)
        db.add_source('EXAMPLE_SOURCE', 'Example source, i.e. a dataset')
        db.add_timeseries_instance('410730', 'D', 'Foo', measurand = 'Q', source = 'EXAMPLE_SOURCE')

        Session.configure(bind=db._TSDB__engine)
        session = Session()

        timeseries = db._TSDB__get_record_by_id('410730', session)
        measurand = db._TSDB__get_attribute('measurand', 'Q', session)
        source = db._TSDB__get_attribute('source', 'EXAMPLE_SOURCE', session)

        query = session.query(TimeseriesInstance). \
                filter_by(measurand = measurand, source=source, timeseries=timeseries)

        record = query.one()
        self.assertEqual(record.timeseries.primary_id, '410730')
        self.assertEqual(record.measurand.short_id, 'Q')
        self.assertEqual(record.source.short_id, 'EXAMPLE_SOURCE')

    def test_read_metadata(self):
        db = TSDB(self.test_tsdb)
        db.add_timeseries('410731')
        db.add_timeseries_instance('410731', 'D', 'Foo', measurand = 'Q', source = 'DATA_SOURCE')
        metadata = db.read_metadata('410730', 'D', measurand = 'Q', source = 'DATA_SOURCE')
        self.assertEqual('', metadata)

        metadata = db.read_metadata('410731', 'D', measurand = 'Q', source = 'DATA_SOURCE')
        self.assertEqual('Foo', metadata)

    def test_get_ts_instance(self):
        db = TSDB(self.test_tsdb)
        ts_instance = db._TSDB__get_ts_instance('410730', 'D', measurand = 'Q', source = 'DATA_SOURCE')
        self.assertEqual('410730', ts_instance.timeseries.primary_id)
        self.assertEqual('Q', ts_instance.measurand.short_id)

        self.assertRaises(MissingDataError, db._TSDB__get_ts_instance, '410731', 'D', measurand = 'Q', source = 'DATA_SOURCE')

        db.add_measurand('P', 'PRECIPITATION', 'Precipitation')
        self.assertRaises(MissingDataError, db._TSDB__get_ts_instance, '410730', 'D', measurand = 'P', source = 'DATA_SOURCE')
