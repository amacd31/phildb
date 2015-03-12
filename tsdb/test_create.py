import os
import shutil
import tempfile
import unittest

from tsdb.database import TSDB
from tsdb.create import create
from tsdb.exceptions import AlreadyExistsError

class CreateDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_create_new(self):
        db_name = os.path.join(self.temp_dir, 'new_project')
        create(db_name)
        db = TSDB(db_name)
        self.assertEqual(os.path.exists(db._TSDB__meta_data_db()), True)

    def test_create_existing_dir(self):
        db_name = os.path.join(self.temp_dir)
        create(db_name)
        db = TSDB(db_name)
        self.assertEqual(os.path.exists(db._TSDB__meta_data_db()), True)

    def test_protect_existing(self):
        db_name = os.path.join(self.test_data_dir, 'test_tsdb')
        with self.assertRaises(AlreadyExistsError) as context:
            create(db_name)

        self.assertEqual(str(context.exception),
            "TSDB already exists at: {0}".format(db_name))
