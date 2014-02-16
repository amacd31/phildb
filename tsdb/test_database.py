import os
import unittest

from .database import TSDB

class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')

    def test_tsdb_exists(self):
        print os.path.join(self.test_data_dir, 'this_tsdb_does_not_exist')
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

