import os
import hashlib
import numpy as np
import shutil
import tempfile
import unittest
from datetime import date, datetime

from . import writer
from . import reader
from .constants import METADATA_MISSING_VALUE

class WriterTest(unittest.TestCase):
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

    def test_bulk_write(self):
        writer.bulk_write(self.tsdb_file, [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, 2.0, 3.0]], 'D')
        with open(self.tsdb_file, 'rb') as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', hashlib.md5(datafile).hexdigest())

    def test_bulk_write_with_missing(self):
        writer.bulk_write(self.tsdb_file, [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, np.nan, 3.0]], 'D')

        data = reader.read_all(self.tsdb_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertTrue(np.isnan(data.values[1][0]))
        self.assertEqual(3.0, data.values[2][0])
        self.assertEqual(METADATA_MISSING_VALUE, data.metaID[1])

    def test_update_single(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2)], [2.5]], 'D')
        self.assertEqual(1, len(modified))
        self.assertEqual([(1388620800, 2.0, 0)], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1][0])

    def test_update_multiple(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2),datetime(2014,1,3)], [2.5, 3.5]], 'D')
        self.assertEqual(2, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388707200, 3.0, 0), modified[1])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1][0])
        self.assertEqual(3.5, data.values[2][0])

    def test_append_single(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4)], [4.0]], 'D')
        self.assertEqual([], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(4.0, data.values[-1][0])

    def test_append_multiple(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [4.0, 5.0, 6.0]], 'D')
        self.assertEqual([], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertEqual(4.0, data.values[3][0])
        self.assertEqual(5.0, data.values[4][0])
        self.assertEqual(6.0, data.values[5][0])

    def test_update_and_append(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [2.5, 3.0, 4.0, 5.0, 6.0]], 'D')

        self.assertEqual(1, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])

        data = reader.read_all(self.tsdb_existing_file)
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

    def test_update_and_append_with_gap(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,5), datetime(2014,1,6)], [5.0, 6.0]], 'D')

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertTrue(np.isnan(data.values[3][0]))
        self.assertEqual(5.0, data.values[4][0])
        self.assertEqual(6.0, data.values[5][0])
        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014,1,4), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014,1,5), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014,1,6), data.index[5].to_pydatetime())

    def test_update_multiple_with_gap(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2),datetime(2014,1,3)], [np.nan, 3.5]], 'D')

        self.assertEqual(2, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388707200, 3.0, 0), modified[1])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertTrue(np.isnan(data.values[1][0]))
        self.assertEqual(3.5, data.values[2][0])

    def test_write_missing(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4),datetime(2014,1,5),datetime(2014,1,6)], [4.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertEqual(4.0, data.values[3][0])
        self.assertTrue(np.isnan(data.values[4][0]))
        self.assertEqual(6.5, data.values[5][0])

    def test_update_unordered(self):
        self.assertRaises(ValueError,
                writer.write,
                self.tsdb_existing_file,
                [[datetime(2014,1,1),
                    datetime(2014,1,3),
                    datetime(2014,1,2),
                    datetime(2014,1,4)],
                    [np.nan, 3.5]],
                'D'
                )

    def test_bulk_write_date(self):
        writer.bulk_write(self.tsdb_file, [[date(2014,1,1), date(2014,1,2), date(2014,1,3)], [1.0, 2.0, 3.0]], 'D')
        with open(self.tsdb_file, 'rb') as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', hashlib.md5(datafile).hexdigest())

    def test_write_missing_value(self):
        modified = writer.write(self.tsdb_existing_file, [[date(2014,1,4),date(2014,1,5),date(2014,1,6)], [4.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertEqual(4.0, data.values[3][0])
        self.assertTrue(np.isnan(data.values[4][0]))
        self.assertEqual(6.5, data.values[5][0])

    def test_write_missing_date(self):
        modified = writer.write(self.tsdb_existing_file, [[date(2014,1,3),date(2014,1,5),date(2014,1,6)], [3.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0][0])
        self.assertEqual(2.0, data.values[1][0])
        self.assertEqual(3.0, data.values[2][0])
        self.assertTrue(np.isnan(data.values[3][0]))
        self.assertTrue(np.isnan(data.values[4][0]))
        self.assertEqual(6.5, data.values[5][0])
