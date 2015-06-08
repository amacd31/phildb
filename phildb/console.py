from datetime import datetime, date
import sys

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from IPython.terminal.embed import InteractiveShellEmbed
ipshell = InteractiveShellEmbed()

from phildb.database import PhilDB

print("")
if len(sys.argv) != 2:
    print("Require a PhilDB database to be specified.\n\nUsage:\n\tphil PHILDB_PATH")
else:
    db = PhilDB(sys.argv[1])
    ipshell("Running timeseries database: {0}\n"
            "Access the 'db' object to operate on the database.\n"
            "\n"
            "Run db.help() for a list of available commands.".format(db)
        )

