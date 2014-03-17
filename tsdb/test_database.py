from datetime import datetime
import os
import shutil
import sqlite3
import tempfile
import unittest

from .database import TSDB
from .create import create

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

        self.assertEqual(context.exception.message,
            "TSDB doesn't exist ({0})".format(db_name))

    def test_missing_meta_data(self):
        db_name = os.path.join(self.test_data_dir, 'missing_meta_data')
        with self.assertRaises(IOError) as context:
            db = TSDB(db_name)

        self.assertEqual(context.exception.message,
            "TSDB doesn't contain meta-database ({0}{1}{2})".format(db_name, os.path.sep, 'tsdb.sqlite'))

    def test_meta_data(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        db = TSDB(db_name)

        self.assertEqual(db.version(), "0.0.2")

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
        pk, primary_id, ts_id = c.fetchone();

        self.assertEqual(primary_id, '410730')
        self.assertEqual(ts_id, 'be29d3018ddb34acbe2174ee6522fd00')

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

        results = db.read_all('410730', 'Q')

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.value[0], 1)
        self.assertEqual(results.value[1], 2)
        self.assertEqual(results.value[2], 3)

    def test_bulk_write(self):
        db = TSDB(self.test_tsdb)

        db.add_timeseries('410731')
        db.bulk_write('410731', 'Q', [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, 2.0, 3.0]])

        results = db.read_all('410731', 'Q')

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
        db.write('410730', 'Q', [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [2.5, 3.0, 4.0, 5.0, 6.0]])

        data = db.read_all('410730', 'Q')
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
        self.assertRaises(ValueError, db.write, 'DOESNOTEXIST', 'Q', [[datetime(2014,1,1), datetime(2014,1,2)], [2.0, 3.0]])

    def test_write_non_existant_measurand(self):
        db = TSDB(self.test_tsdb)
        self.assertRaises(ValueError, db.write, '410730', 'DOESNOTEXIST', [[datetime(2014,1,1), datetime(2014,1,2)], [2.0, 3.0]])

    def test_list(self):
        db = TSDB(self.test_tsdb)
        ts_list = db.list()
        self.assertEqual(['410730'], ts_list)
