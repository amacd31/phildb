import os
import md5
import unittest
from datetime import datetime

from . import reader

class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.tsdb_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample.tsdb')

    def test_read_all(self):
        data = reader.read_all(self.tsdb_file)

        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())

        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])

