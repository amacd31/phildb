import os
import md5
import shutil
import tempfile
import unittest
from datetime import datetime

from . import writer

class WriterTest(unittest.TestCase):
    def setUp(self):
        self.tsdb_path = tempfile.mkdtemp()
        self.tsdb_file = os.path.join(self.tsdb_path, 'write_test.tsdb')

    def tearDown(self):
        try:
            shutil.rmtree(self.tsdb_path)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_bulk_write(self):
        writer.bulk_write(self.tsdb_file, [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, 2.0, 3.0]])
        with open(self.tsdb_file) as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', md5.md5(datafile).hexdigest())

