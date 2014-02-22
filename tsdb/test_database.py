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

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
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

        self.assertEqual(db.version(), "0.0.1")

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

    def test_read_all(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        db = TSDB(db_name)

        results = db.read_all('410730')

        self.assertEqual(results.index[0].year, 2014)
        self.assertEqual(results.index[0].month, 1)
        self.assertEqual(results.index[0].day, 1)
        self.assertEqual(results.index[1].day, 2)
        self.assertEqual(results.index[2].day, 3)

        self.assertEqual(results.value[0], 1)
        self.assertEqual(results.value[1], 2)
        self.assertEqual(results.value[2], 3)

