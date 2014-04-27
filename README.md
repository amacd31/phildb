# TSDB project
Timeseries database project: For storing potentially changing timeseries data.
For example hydrological data such as streamflow where the timeseries may be
revised as quality control processes improve the recorded dataset.

At present only daily data is supported.

## Dependencies
Requires Python 2.7 or greater (mostly tested with Python 2.7 on Linux).
Test suite status when run with Python 2.7, 3.2 and 3.3 on Ubuntu (using travis):
![Build Status](https://travis-ci.org/amacd31/tsdb.svg?branch=master)

All the python dependencies are recorded in the python\_requirements file.

The virtualenv package can be used to create an isolated install of required Python
packages.

## Installation
Create a virtual environment with dependencies installed:

    make venv

Test everything is working:

    make test

Build the documentation:

    make docs

View the generated documentation at doc/build/html/index.html

For additional details see the INSTALL file.

# Usage
Load virtual environment along with adding TSDB tools to your path:

    . load_env

Create a new TSDB:

    tsdb-create new_tsdb

Open the newly created TSDB:

    tsdb new_tsdb

See examples/hrs/README for details on setting up a test tsdb.
The directory examples/hrs/ also contains an example script for preparing the
database and loading data.
