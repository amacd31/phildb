from datetime import datetime, date
import sys

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from IPython.terminal.embed import InteractiveShellEmbed
ipshell = InteractiveShellEmbed()

from tsdb.database import TSDB

print("")
if len(sys.argv) != 2:
    print("Require a tsdb database to be specified.\n\nUsage:\n\ttsdb TSDB_PATH")
else:
    db = TSDB(sys.argv[1])
    ipshell("Running timeseries database: {0}\n"
            "Access the 'db' object to operate on the database.\n"
            "\n"
            "Run db.help() for a list of available commands.".format(db)
        )

