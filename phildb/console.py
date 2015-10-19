import argparse
from datetime import datetime, date
import sys

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from IPython.terminal.embed import InteractiveShellEmbed
ipshell = InteractiveShellEmbed()

from phildb import __version__
from phildb.database import PhilDB

def main():
    parser = argparse.ArgumentParser(description='Open PhilDB database.')
    parser.add_argument('dbname', help="PhilDB database to open", nargs='?')
    parser.add_argument('--version', action='store_true', help="Print version and exit.")

    args = parser.parse_args()

    if args.version:
        print("PhilDB version: {0}".format(__version__))
        exit()

    if args.dbname is None:
        print(parser.print_help())
        exit()

    db = PhilDB(args.dbname)
    ipshell("Running timeseries database: {0}\n"
            "Access the 'db' object to operate on the database.\n"
            "\n"
            "Run db.help() for a list of available commands.".format(db)
        )

if __name__ == "__main__":
    main()
