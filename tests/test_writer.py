import os
import hashlib
import numpy as np
import shutil
import tempfile
import unittest
from datetime import date, datetime

from tsdb import writer
from tsdb import reader
from tsdb.constants import METADATA_MISSING_VALUE
from tsdb.exceptions import DataError

class WriterTest(unittest.TestCase):
    def setUp(self):
        self.tsdb_path = tempfile.mkdtemp()
        self.tsdb_existing_file = os.path.join(self.tsdb_path, 'existing_test.tsdb')
        shutil.copy(os.path.join(os.path.dirname(__file__),
            'test_data',
            'sample.tsdb'),
            self.tsdb_existing_file)

        self.tsdb_30min_existing_file = os.path.join(self.tsdb_path, '30min_existing_test.tsdb')
        shutil.copy(os.path.join(os.path.dirname(__file__),
            'test_data',
            'sample_30min.tsdb'),
            self.tsdb_30min_existing_file)

        self.tsdb_monthly_existing_file = os.path.join(self.tsdb_path, 'monthly_existing_test.tsdb')
        shutil.copy(os.path.join(os.path.dirname(__file__),
            'test_data',
            'sample_monthly.tsdb'),
            self.tsdb_monthly_existing_file)

        self.tsdb_monthly_start_existing_file = os.path.join(self.tsdb_path, 'monthly_start_existing_test.tsdb')
        shutil.copy(os.path.join(os.path.dirname(__file__),
            'test_data',
            'sample_monthly_start.tsdb'),
            self.tsdb_monthly_start_existing_file)

        self.tsdb_file = os.path.join(self.tsdb_path, 'write_test.tsdb')

    def tearDown(self):
        try:
            shutil.rmtree(self.tsdb_path)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_new_write(self):
        writer.write(self.tsdb_file, [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, 2.0, 3.0]], 'D')
        with open(self.tsdb_file, 'rb') as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', hashlib.md5(datafile).hexdigest())

    def test_new_write_with_missing(self):
        writer.write(self.tsdb_file, [[datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], [1.0, np.nan, 3.0]], 'D')

        data = reader.read_all(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.0, data.values[2])

    def test_update_single(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2)], [2.5]], 'D')
        self.assertEqual(1, len(modified))
        self.assertEqual([(1388620800, 2.0, 0)], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1])

    def test_update_multiple(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2),datetime(2014,1,3)], [2.5, 3.5]], 'D')
        self.assertEqual(2, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388707200, 3.0, 0), modified[1])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1])
        self.assertEqual(3.5, data.values[2])

    def test_append_single(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4)], [4.0]], 'D')
        self.assertEqual([], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(4.0, data.values[-1])

    def test_append_multiple(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [4.0, 5.0, 6.0]], 'D')
        self.assertEqual([], modified)

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertEqual(5.0, data.values[4])
        self.assertEqual(6.0, data.values[5])

    def test_update_and_append(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], [2.5, 3.0, 4.0, 5.0, 6.0]], 'D')

        self.assertEqual(1, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.5, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertEqual(5.0, data.values[4])
        self.assertEqual(6.0, data.values[5])
        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014,1,4), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014,1,5), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014,1,6), data.index[5].to_pydatetime())

    def test_update_and_append_with_gap(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,5), datetime(2014,1,6)], [5.0, 6.0]], 'D')

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertTrue(np.isnan(data.values[3]))
        self.assertEqual(5.0, data.values[4])
        self.assertEqual(6.0, data.values[5])
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
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.5, data.values[2])

    def test_write_missing(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,4),datetime(2014,1,5),datetime(2014,1,6)], [4.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_update_unordered(self):
        self.assertRaises(DataError,
                writer.write,
                self.tsdb_existing_file,
                [[datetime(2014,1,1),
                    datetime(2014,1,3),
                    datetime(2014,1,2),
                    datetime(2014,1,4)],
                    [np.nan, 3.5]],
                'D'
                )

    def test_new_write_date(self):
        writer.write(self.tsdb_file, [[date(2014,1,1), date(2014,1,2), date(2014,1,3)], [1.0, 2.0, 3.0]], 'D')
        with open(self.tsdb_file, 'rb') as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', hashlib.md5(datafile).hexdigest())

    def test_write_missing_value(self):
        modified = writer.write(self.tsdb_existing_file, [[date(2014,1,4),date(2014,1,5),date(2014,1,6)], [4.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_write_missing_date(self):
        modified = writer.write(self.tsdb_existing_file, [[date(2014,1,3),date(2014,1,5),date(2014,1,6)], [3.0, np.nan, 6.5]], 'D')

        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertTrue(np.isnan(data.values[3]))
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_write_overlapping_hourly(self):
        input_a = [
                    [datetime(2014,1,1,0,0,0),
                        datetime(2014,1,1,1,0,0),
                        datetime(2014,1,1,2,0,0)
                    ],
                    [1.0,
                        2.0,
                        3.0]
                    ]
        input_b = [
                    [datetime(2014,1,1,2,0,0),
                        datetime(2014,1,1,3,0,0),
                        datetime(2014,1,1,4,0,0),
                        datetime(2014,1,1,5,0,0)
                    ],
                    [4.0,
                        5.0,
                        6.0,
                        7.0]
                    ]

        writer.write(self.tsdb_file, input_a, 'H')
        modified = writer.write(self.tsdb_file, input_b, 'H')
        self.assertEqual(1, len(modified))
        self.assertEqual([(1388541600, 3.0, 0)], modified)

        data = reader.read_all(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(4.0, data.values[2])
        self.assertEqual(5.0, data.values[3])
        self.assertEqual(6.0, data.values[4])
        self.assertEqual(7.0, data.values[5])

    def test_append_30min(self):
        new_data = [
                    [
                        datetime(2014,8,30,6,0,0),
                        datetime(2014,8,30,6,30,0)
                    ],
                    [
                        6.0,
                        6.30
                    ]
                ]

        modified = writer.write(self.tsdb_30min_existing_file, new_data, '30min')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_30min_existing_file)
        self.assertEqual(148, len(data))

        self.assertEqual(17.2, data.values[0])
        self.assertTrue(np.isnan(data.values[-3]))
        self.assertEqual(6.0, data.values[-2])
        self.assertEqual(6.3, data.values[-1])

    def test_write_monthly_end_data(self):
        new_data = [
                    [
                        datetime(2014,6,30),
                        datetime(2014,7,31),
                        datetime(2014,8,31),
                        datetime(2014,9,30)
                    ],
                    [
                        6.0,
                        7.3,
                        8.0,
                        9.1
                    ]
                ]

        modified = writer.write(self.tsdb_file, new_data, 'M')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_file)
        self.assertEqual(4, len(data))

        self.assertEqual(6.0, data.values[0])
        self.assertEqual(7.3, data.values[1])
        self.assertEqual(8.0, data.values[2])
        self.assertEqual(9.1, data.values[3])

    def test_write_monthly_start_data(self):
        new_data = [
                    [
                        datetime(2014,6,1),
                        datetime(2014,7,1),
                        datetime(2014,8,1),
                        datetime(2014,9,1)
                    ],
                    [
                        6.0,
                        7.3,
                        8.0,
                        9.1
                    ]
                ]

        modified = writer.write(self.tsdb_file, new_data, 'MS')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_file)
        self.assertEqual(4, len(data))

        self.assertEqual(6.0, data.values[0])
        self.assertEqual(7.3, data.values[1])
        self.assertEqual(8.0, data.values[2])
        self.assertEqual(9.1, data.values[3])


    def test_append_monthly_end_data(self):
        new_data = [
                    [
                        datetime(1901,1,31),
                        datetime(1901,2,28),
                    ],
                    [
                        31.1,
                        28.2
                    ]
                ]

        modified = writer.write(self.tsdb_monthly_existing_file, new_data, 'M')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_monthly_existing_file)
        self.assertEqual(14, len(data))

        self.assertEqual(31.1, data.values[-2])
        self.assertEqual(28.2, data.values[-1])

    def test_append_monthly_start_data(self):
        new_data = [
                    [
                        datetime(1901,1,1),
                        datetime(1901,2,1),
                    ],
                    [
                        31.1,
                        28.2
                    ]
                ]

        modified = writer.write(self.tsdb_monthly_start_existing_file, new_data, 'MS')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_monthly_start_existing_file)

        self.assertEqual(datetime(1900,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(1901,2,1), data.index[-1].to_pydatetime())

        self.assertEqual(14, len(data))

    def test_write_irregular_data(self):
        new_data = [
                    [
                        datetime(1900,1,1),
                        datetime(1900,3,1),
                        datetime(1900,4,1),
                        datetime(1900,6,1),
                    ],
                    [
                        1.0,
                        2.0,
                        3.0,
                        4.0
                    ]
                ]

        modified = writer.write(self.tsdb_file, new_data, 'IRR')
        self.assertEqual(0, len(modified))

        data = reader.read_all(self.tsdb_file)

        self.assertEqual(datetime(1900,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(1900,3,1), data.index[1].to_pydatetime())
        self.assertEqual(datetime(1900,4,1), data.index[2].to_pydatetime())
        self.assertEqual(datetime(1900,6,1), data.index[3].to_pydatetime())

        self.assertEqual(4, len(data))

        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])

    def test_irregular_update_and_append(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], [2.5, 3.0, 5.0, 7.0, 8.0]], 'IRR')

        self.assertEqual(1, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.5, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(5.0, data.values[3])
        self.assertEqual(7.0, data.values[4])
        self.assertEqual(8.0, data.values[5])
        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014,1,5), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014,1,7), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014,1,8), data.index[5].to_pydatetime())

    def test_irregular_update_nan(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], [2, np.nan, 5.0, 7.0, 8.0]], 'IRR')

        self.assertEqual(1, len(modified))
        self.assertEqual((1388707200, 3.0, 0), modified[0])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertTrue(np.isnan(data.values[2]))
        self.assertEqual(5.0, data.values[3])
        self.assertEqual(7.0, data.values[4])
        self.assertEqual(8.0, data.values[5])
        self.assertEqual(datetime(2014,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,2), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
        self.assertEqual(datetime(2014,1,5), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2014,1,7), data.index[4].to_pydatetime())
        self.assertEqual(datetime(2014,1,8), data.index[5].to_pydatetime())

    def test_irregular_update_of_nan(self):
        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], [2, np.nan, 5.0, 7.0, 8.0]], 'IRR')

        modified = writer.write(self.tsdb_existing_file, [[datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], [2, 3.5, 5.0, 7.0, 8.0]], 'IRR')

        self.assertEqual(1, len(modified))
        self.assertEqual(1388707200, modified[0][0])
        self.assertTrue(np.isnan(modified[0][1]))
        # TODO: Meta value should actually be the missing value meta-value.
        self.assertEqual(0, modified[0][2])

        data = reader.read_all(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.5, data.values[2])
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())
