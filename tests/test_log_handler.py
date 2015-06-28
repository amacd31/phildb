import calendar
import os
import shutil
import tables
import tempfile
import unittest
from datetime import datetime

from phildb.log_handler import LogHandler

class LogHandlerTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp_dir)
        except OSError as e:
            if e.errno != 2: # Code 2: No such file or directory.
                raise

    def test_logging(self):
        log_file = os.path.join(self.tmp_dir, 'log_file.hdf5')
        create_datetime = calendar.timegm(datetime(2015, 6, 28, 15, 25, 00).utctimetuple())

        log_entries = {
            'C': [(1388620800, 2.0, 0), (1388707200, 3.0, 0)],
            'U': []
        }

        with LogHandler(log_file, 'w') as writer:
            writer.create_skeleton()

        with LogHandler(log_file, 'a') as writer:
            writer.write(log_entries, create_datetime)

        update_datetime = calendar.timegm(datetime(2015, 6, 28, 16, 25, 00).utctimetuple())
        log_entries = {
            'C': [(1388620800, 3.0, 0), (1388707200, 4.0, 0)],
            'U': []
        }

        with LogHandler(log_file, 'a') as writer:
            writer.write(log_entries, update_datetime)

        with tables.open_file(log_file, 'r') as hdf5_file:
            log_grp = hdf5_file.get_node('/data')

            self.assertEqual(len(log_grp.log), 4)

            self.assertSequenceEqual(
                log_grp.log[0],
                (1388620800, 2.0, 0, create_datetime)
            )
            self.assertSequenceEqual(
                log_grp.log[1],
                (1388707200, 3.0, 0, create_datetime)
            )
            self.assertSequenceEqual(
                log_grp.log[2],
                (1388620800, 3.0, 0, update_datetime)
            )
            self.assertSequenceEqual(
                log_grp.log[3],
                (1388707200, 4.0, 0, update_datetime)
            )
