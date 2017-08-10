import gc
import os
import hashlib
import numpy as np
import pandas as pd
import shutil
import tempfile
import unittest
from datetime import date, datetime

from phildb import writer
from phildb import reader
from phildb.constants import METADATA_MISSING_VALUE
from phildb.exceptions import DataError

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
        # On Windows files can't be removed while still open.
        # The time between the db object going out of scope and tear down
        # occurring is too short for garbage collection to have run.
        # As a result SQLAlchemy has not released the sqlite file by the
        # time tear down occurs.
        # This results in an error on Windows:
        #     PermissionError: [WinError 32] The process cannot access the file
        #     because it is being used by another process:
        # Therefore garbage collect before trying to remove temporary files.
        gc.collect()
        try:
            shutil.rmtree(self.tsdb_path)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_new_write(self):
        writer.write(self.tsdb_file, pd.Series(index = [datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], data = [1.0, 2.0, 3.0]), 'D')
        with open(self.tsdb_file, 'rb') as file:
            datafile = file.read()

        self.assertEqual('06606801154cbfdc8e1b8c7b1e3c1956', hashlib.md5(datafile).hexdigest())

    def test_new_write_with_missing(self):
        writer.write(self.tsdb_file, pd.Series(index = [datetime(2014,1,1), datetime(2014,1,2), datetime(2014,1,3)], data = [1.0, np.nan, 3.0]), 'D')

        data = reader.read(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.0, data.values[2])

    def test_new_write_and_update_minute_data(self):
        writer.write(self.tsdb_file, pd.Series(index = [datetime(2014,1,1,18,1,0), datetime(2014,1,1,18,2,0), datetime(2014,1,1,18,3,0)], data = [1.0, np.nan, 3.0]), '1T')

        data = reader.read(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.0, data.values[2])

        self.assertEqual(datetime(2014,1,1,18,1,0), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,1,18,2,0), data.index[1].to_pydatetime())
        self.assertEqual(datetime(2014,1,1,18,3,0), data.index[2].to_pydatetime())

        writer.write(self.tsdb_file, pd.Series(index = [datetime(2014,1,1,18,3,0), datetime(2014,1,1,18,4,0), datetime(2014,1,1,18,5,0)], data = [3.5, 4.0, 5.0]), '1T')

        data = reader.read(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.5, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertEqual(5.0, data.values[4])

        self.assertEqual(datetime(2014,1,1,18,1,0), data.index[0].to_pydatetime())
        self.assertEqual(datetime(2014,1,1,18,5,0), data.index[-1].to_pydatetime())

    def test_update_single(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2)], data = [2.5]), 'D')
        modified = log_entries['U']
        self.assertEqual(1, len(modified))
        self.assertEqual([(1388620800, 2.0, 0)], modified)

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1])

    def test_update_multiple(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2),datetime(2014,1,3)], data = [2.5, 3.5]), 'D')
        modified = log_entries['U']
        self.assertEqual(2, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388707200, 3.0, 0), modified[1])

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(2.5, data.values[1])
        self.assertEqual(3.5, data.values[2])

    def test_append_single(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,4)], data = [4.0]), 'D')
        modified = log_entries['U']
        self.assertEqual([], modified)

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(4.0, data.values[-1])

    def test_append_multiple(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], data = [4.0, 5.0, 6.0]), 'D')
        modified = log_entries['U']
        self.assertEqual([], modified)

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertEqual(5.0, data.values[4])
        self.assertEqual(6.0, data.values[5])

    def test_update_and_append(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,4), datetime(2014,1,5), datetime(2014,1,6)], data = [2.5, 3.0, 4.0, 5.0, 6.0]), 'D')
        modified = log_entries['U']

        self.assertEqual(1, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])

        data = reader.read(self.tsdb_existing_file)
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
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,5), datetime(2014,1,6)], data = [5.0, 6.0]), 'D')
        modified = log_entries['U']

        data = reader.read(self.tsdb_existing_file)
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
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2),datetime(2014,1,3)], data = [np.nan, 3.5]), 'D')
        modified = log_entries['U']

        self.assertEqual(2, len(modified))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388707200, 3.0, 0), modified[1])

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertTrue(np.isnan(data.values[1]))
        self.assertEqual(3.5, data.values[2])

    def test_write_missing(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,4),datetime(2014,1,5),datetime(2014,1,6)], data = [4.0, np.nan, 6.5]), 'D')
        modified = log_entries['U']

        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_write_missing_value(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [date(2014,1,4),date(2014,1,5),date(2014,1,6)], data = [4.0, np.nan, 6.5]), 'D')
        modified = log_entries['U']

        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_write_missing_date(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [date(2014,1,3),date(2014,1,5),date(2014,1,6)], data = [3.0, np.nan, 6.5]), 'D')
        modified = log_entries['U']

        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertTrue(np.isnan(data.values[3]))
        self.assertTrue(np.isnan(data.values[4]))
        self.assertEqual(6.5, data.values[5])

    def test_write_overlapping_hourly(self):
        input_a = pd.Series(
                    index = [
                        datetime(2014,1,1,0,0,0),
                        datetime(2014,1,1,1,0,0),
                        datetime(2014,1,1,2,0,0)
                    ],
                    data = [
                        1.0,
                        2.0,
                        3.0
                    ]
                )
        input_b = pd.Series(
                    index = [
                        datetime(2014,1,1,2,0,0),
                        datetime(2014,1,1,3,0,0),
                        datetime(2014,1,1,4,0,0),
                        datetime(2014,1,1,5,0,0)
                    ],
                    data = [
                        4.0,
                        5.0,
                        6.0,
                        7.0
                    ]
                )

        writer.write(self.tsdb_file, input_a, 'H')
        log_entries = writer.write(self.tsdb_file, input_b, 'H')
        modified = log_entries['U']
        self.assertEqual(1, len(modified))
        self.assertEqual([(1388541600, 3.0, 0)], modified)

        data = reader.read(self.tsdb_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(4.0, data.values[2])
        self.assertEqual(5.0, data.values[3])
        self.assertEqual(6.0, data.values[4])
        self.assertEqual(7.0, data.values[5])

    def test_append_30min(self):
        new_data = pd.Series(
                    index = [
                        datetime(2014,8,30,6,0,0),
                        datetime(2014,8,30,6,30,0)
                    ],
                    data = [
                        6.0,
                        6.30
                    ]
                )

        log_entries = writer.write(self.tsdb_30min_existing_file, new_data, '30min')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_30min_existing_file)
        self.assertEqual(148, len(data))

        self.assertEqual(17.2, data.values[0])
        self.assertTrue(np.isnan(data.values[-3]))
        self.assertEqual(6.0, data.values[-2])
        self.assertEqual(6.3, data.values[-1])

    def test_write_monthly_end_data(self):
        new_data = pd.Series(
                    index = [
                        datetime(2014,6,30),
                        datetime(2014,7,31),
                        datetime(2014,8,31),
                        datetime(2014,9,30)
                    ],
                    data = [
                        6.0,
                        7.3,
                        8.0,
                        9.1
                    ]
                )

        log_entries = writer.write(self.tsdb_file, new_data, 'M')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_file)
        self.assertEqual(4, len(data))

        self.assertEqual(6.0, data.values[0])
        self.assertEqual(7.3, data.values[1])
        self.assertEqual(8.0, data.values[2])
        self.assertEqual(9.1, data.values[3])

    def test_write_monthly_start_data(self):
        new_data = pd.Series(
                    index = [
                        datetime(2014,6,1),
                        datetime(2014,7,1),
                        datetime(2014,8,1),
                        datetime(2014,9,1)
                    ],
                    data = [
                        6.0,
                        7.3,
                        8.0,
                        9.1
                    ]
                )

        log_entries = writer.write(self.tsdb_file, new_data, 'MS')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_file)
        self.assertEqual(4, len(data))

        self.assertEqual(6.0, data.values[0])
        self.assertEqual(7.3, data.values[1])
        self.assertEqual(8.0, data.values[2])
        self.assertEqual(9.1, data.values[3])


    def test_append_monthly_end_data(self):
        new_data = pd.Series(
                    index = [
                        datetime(1901,1,31),
                        datetime(1901,2,28),
                    ],
                    data = [
                        31.1,
                        28.2
                    ]
                )

        log_entries = writer.write(self.tsdb_monthly_existing_file, new_data, 'M')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_monthly_existing_file)
        self.assertEqual(14, len(data))

        self.assertEqual(31.1, data.values[-2])
        self.assertEqual(28.2, data.values[-1])

    def test_append_monthly_start_data(self):
        new_data = pd.Series(
                    index = [
                        datetime(1901,1,1),
                        datetime(1901,2,1),
                    ],
                    data = [
                        31.1,
                        28.2
                    ]
                )

        log_entries = writer.write(self.tsdb_monthly_start_existing_file, new_data, 'MS')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_monthly_start_existing_file)

        self.assertEqual(datetime(1900,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(1901,2,1), data.index[-1].to_pydatetime())

        self.assertEqual(14, len(data))

    def test_write_irregular_data(self):
        new_data = pd.Series(
                    index = [
                        datetime(1900,1,1),
                        datetime(1900,3,1),
                        datetime(1900,4,1),
                        datetime(1900,6,1),
                    ],
                    data = [
                        1.0,
                        2.0,
                        3.0,
                        4.0
                    ]
                )

        log_entries = writer.write(self.tsdb_file, new_data, 'IRR')
        modified = log_entries['U']
        self.assertEqual(0, len(modified))

        data = reader.read(self.tsdb_file)

        self.assertEqual(datetime(1900,1,1), data.index[0].to_pydatetime())
        self.assertEqual(datetime(1900,3,1), data.index[1].to_pydatetime())
        self.assertEqual(datetime(1900,4,1), data.index[2].to_pydatetime())
        self.assertEqual(datetime(1900,6,1), data.index[3].to_pydatetime())

        self.assertEqual(4, len(data))

        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(4.0, data.values[3])

    def test_irregular_append(self):
        initial_data = reader.read(self.tsdb_existing_file)
        log_entries = writer.write(
            self.tsdb_existing_file,
            pd.Series(
                index = [
                    datetime(2014,1,5),
                    datetime(2014,1,7),
                    datetime(2014,1,8)
                ],
                data = [
                    5.0,
                    7.0,
                    8.0
                ]
            ),
            'IRR'
        )
        created = log_entries['C']
        modified = log_entries['U']

        self.assertEqual(0, len(modified))
        self.assertEqual(3, len(created))
        self.assertEqual((1388880000, 5.0, 0), created[0])

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(len(initial_data) + 3, len(data))
        self.assertEqual(3.0, data.values[2])
        self.assertEqual(5.0, data.values[3])
        self.assertEqual(7.0, data.values[4])
        self.assertEqual(8.0, data.values[5])

    def test_irregular_update_and_append(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], data = [2.5, 3.0, 5.0, 7.0, 8.0]), 'IRR')
        created = log_entries['C']
        modified = log_entries['U']

        self.assertEqual(1, len(modified))
        self.assertEqual(4, len(created))
        self.assertEqual((1388620800, 2.0, 0), modified[0])
        self.assertEqual((1388620800, 2.5, 0), created[0])

        data = reader.read(self.tsdb_existing_file)
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
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], data = [2, np.nan, 5.0, 7.0, 8.0]), 'IRR')
        modified = log_entries['U']

        self.assertEqual(1, len(modified))
        self.assertEqual((1388707200, 3.0, 0), modified[0])

        data = reader.read(self.tsdb_existing_file)
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
        writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], data = [2, np.nan, 5.0, 7.0, 8.0]), 'IRR')

        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2), datetime(2014,1,3), datetime(2014,1,5), datetime(2014,1,7), datetime(2014,1,8)], data = [2, 3.5, 5.0, 7.0, 8.0]), 'IRR')
        modified = log_entries['U']

        self.assertEqual(1, len(modified))
        self.assertEqual(1388707200, modified[0][0])
        self.assertTrue(np.isnan(modified[0][1]))
        self.assertEqual(9999, modified[0][2])

        data = reader.read(self.tsdb_existing_file)
        self.assertEqual(1.0, data.values[0])
        self.assertEqual(2.0, data.values[1])
        self.assertEqual(3.5, data.values[2])
        self.assertEqual(datetime(2014,1,3), data.index[2].to_pydatetime())

    def test_update_over_nan(self):
        # Append a nan value
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [date(2014,1,4)], data = [np.nan]), 'D')

        # Test the nan value was written
        data = reader.read(self.tsdb_existing_file)
        self.assertTrue(np.isnan(data.values[3]))

        # Replace the nan value
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [date(2014,1,4)], data = [4.0]), 'D')

        updated_data = reader.read(self.tsdb_existing_file)
        self.assertEqual(4.0, updated_data.values[3])

        modified = log_entries['U']
        self.assertEqual(1, len(modified))

    def test_log_entries_for_update_nan_multiple_times(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2),datetime(2014,1,3)], data = [np.nan, 3.5]), 'D')
        new_entries = log_entries['C']
        self.assertEqual(2, len(new_entries))

        log_entries = writer.write(self.tsdb_existing_file, pd.Series(index = [datetime(2014,1,2),datetime(2014,1,3)], data = [np.nan, 3.5]), 'D')
        new_entries = log_entries['C']
        self.assertEqual(1, len(new_entries))

    def test_empty_series_write(self):
        log_entries = writer.write(self.tsdb_existing_file, pd.Series([]), 'D')
        self.assertEqual(0, len(log_entries['C']))
        self.assertEqual(0, len(log_entries['U']))

    def test_float32_irregular_write(self):
        """
            Test irregular write of float32 data.

            See: https://github.com/amacd31/phildb/issues/16
        """

        sample = pd.Series(
            pd.np.array(
                [x + 0.1 for x in range(10)],
                dtype=pd.np.float32
            ),
            index=pd.date_range(
                '2017-08-06 06:50:00',
                periods=10,
                freq='1T'
            )
        )

        log_entries = writer.write(self.tsdb_existing_file, sample, 'IRR')
        data = reader.read(self.tsdb_existing_file)

        self.assertEqual(datetime(2017,8,6,6,50,0,0), data.index[3].to_pydatetime())
        self.assertEqual(datetime(2017,8,6,6,51,0,0), data.index[4].to_pydatetime())
