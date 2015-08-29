"""
    Unit tests to catch performance problems.
"""

import os
import numpy as np
import shutil
import tempfile
import unittest
from datetime import datetime
import time

from phildb import writer
from phildb import reader

class SpeedTest(unittest.TestCase):
    def setUp(self):
        self.tsdb_path = tempfile.mkdtemp()
        self.tsdb_existing_file = os.path.join(self.tsdb_path, 'existing_test.tsdb')
        shutil.copy(os.path.join(os.path.dirname(__file__),
            'test_data',
            'sample.tsdb'),
            self.tsdb_existing_file)

        self.tsdb_file = os.path.join(self.tsdb_path, 'write_test.tsdb')

    def tearDown(self):
        try:
            shutil.rmtree(self.tsdb_path)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_append_with_large_gap(self):
        writer.write(self.tsdb_file, [[datetime(2005,1,1)], [1.0]], 'H')
        start_time = time.time()
        writer.write(self.tsdb_file, [[datetime(2014,12,31)], [2.0]], 'H')
        end_time = time.time()

        # Prior to the fix committed with this test, on my Macbook Air,
        # the run time here was around 1.3 seconds. After the fix
        # it is down to almost half a second (around 0.56 seconds for
        # the total test run time).
        # The performance improvement is larger with bigger gaps.
        self.assertLessEqual((end_time - start_time), 1)

        # A few spot checks to make sure the test actually ran as expected.
        data = reader.read(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(2.0, data.values[-1])
        self.assertEqual(datetime(2005,1,1,0,0), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,12,31), data.index[-1].to_pydatetime())
