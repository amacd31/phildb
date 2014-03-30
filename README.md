# TSDB project
Timeseries database project: For storing potentially changing timeseries data.
For example hydrological data such as streamflow where the timeseries may be
revised as quality control processes improve the recorded dataset.

At present only daily data is supported.

## Dependencies
Requires Python 2.7 or greater (so far only tested with Python 2.7 on Linux).
The virtualenv package is used to create an isolated install of required Python
packages.

All the python dependencies are recorded in the python\_requirements file.

## Installation
Create a virtual environment with dependencies installed:

    make venv

Test everything is working:

    make test

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
