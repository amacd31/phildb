PhilDB project
==============

|DOI| |PYPI Version| |PYPI Status| |PYPI Python versions| |PYPI License| |Build Status| |Appveyor Status| |Code Coverage|

Timeseries database project: For storing potentially changing timeseries
data. For example hydrological data, like streamflow data, where the
timeseries may be revised as quality control processes improve the
recorded dataset over time.

PhilDB should be capable of storing data at any frequency supported by
Pandas. At this time only daily data has been extensively tested with
some limited sub-daily usage.

Further information about the design of PhilDB can be found in the paper:
`PhilDB: the time series database with built-in change logging <https://peerj.com/articles/cs-52/>`_.
That paper explores existing time series database solutions, discusses the
motivation for PhilDB, describes the architecture and philosophy of the PhilDB
software, and includes an evaluation between InfluxDB, PhilDB, and SciDB.

Dependencies
------------

Requires Python 3.7 or greater (mostly tested on Mac OSX and Linux).
Test suite runs on Linux using Travis CI with Python 3.6, 3.7, and 3.8.
Test suite runs on Windows using Appveyor with Python 3.7.

All the python dependencies are recorded in the python\_requirements
file.

Installation
------------

PhilDB is pip installable.

The latest stable version can be installed from pypi with::

    pip install phildb

The latest stable version can also be installed from conda with::

    conda install -c amacd31 phildb

The latest development version can be installed from github with::

    pip install git+https://github.com/amacd31/phildb.git@dev

The latest development version can be installed from conda with::

    conda install -c amacd31/label/dev phildb

Development environment
^^^^^^^^^^^^^^^^^^^^^^^

A number of processes for a development environment with tests and documentation generation have been automated in a Makefile.

The virtualenv package can be used to create an isolated install of
required Python packages.

Create a virtual environment with dependencies installed:

::

    make venv

Test everything is working:

::

    make test

Build the documentation:

::

    make docs

View the generated documentation at doc/build/html/index.html

For additional details see the INSTALL file.

Usage
=====

Create a new PhilDB

::

    phil-create new_tsdb

Open the newly created PhilDB

::

    phildb new_tsdb

If using the development environment built with make, Load it along with adding PhilDB tools to your path:

::

    . load_env

Examples
========

See the examples directory for code on setting up test phil databases with
different data sets. Each example comes with a README file outlining the
steps to acquire some data and load it. The loading scripts in each
example can be used as a basis for preparing a timeseries database and
loading it with data.

The examples/hrs/ example also contains an example script (autocorr.py)
for processing the HRS data using phildb. The script calculates
auto-correlation for all the streamflow timeseries in the HRS dataset.

Presently there are three sets of example code, acorn-sat,
bom\_observations, and hrs.

ACORN-SAT
---------

`ACORN-SAT Example.ipynb <https://github.com/amacd31/phildb/blob/master/examples/acorn-sat/ACORN-SAT%20Example.ipynb>`_ located in examples/acorn-sat demonstrates loading minimum
and maximum daily temperature records for 112 stations around Australia.

The dataset used in this example is the Australian Climate Observations
Reference Network – Surface Air Temperature (ACORN-SAT) as found on the
Australian Bureau of Meteorology website
`ACORN-SAT website <http://www.bom.gov.au/climate/change/acorn-sat/>`_.

BOM Observations
----------------

`Bureau of Meterology observations example.ipynb <https://github.com/amacd31/phildb/blob/master/examples/bom_observations/Bureau%20of%20Meterology%20observations%20example.ipynb>`_
located in examples/bom\_observations demonstrates loading
half hourly air temperature data from a 72 hour observations JSON file.

The data used in this example is a 72 hour observations JSON file from
the Australian Bureau of Meteorology website (e.g. JSON file as linked
on this page: `Sydney Airport
observations <http://www.bom.gov.au/products/IDN60901/IDN60901.94767.shtml#other_formats>`_

HRS
---

`HRS Example.ipynb <https://github.com/amacd31/phildb/blob/master/examples/hrs/HRS%20Example.ipynb>`_
located in examples/hrs demonstrates loading daily
streamflow data for 221 streamflow stations around Australia.

The dataset used in this example is the Hydrologic Reference Stations
(HRS) dataset as found on the Australian Bureau of Meteorology website
`HRS website <http://www.bom.gov.au/water/hrs/>`_.

This example also includes a script to calculate the auto-correlation
for all the streamflow timeseries in the HRS dataset.

.. |PYPI Version| image:: https://img.shields.io/pypi/v/phildb.svg
    :target: https://pypi.python.org/pypi/PhilDB

.. |PYPI Status| image:: https://img.shields.io/pypi/status/phildb.svg
    :target: https://pypi.python.org/pypi/PhilDB

.. |PYPI Python versions| image:: https://img.shields.io/pypi/pyversions/phildb.svg
    :target: https://pypi.python.org/pypi/PhilDB

.. |PYPI License| image:: https://img.shields.io/pypi/l/phildb.svg
    :target: https://github.com/amacd31/phildb/blob/master/LICENSE

.. |Build Status| image:: https://img.shields.io/travis/amacd31/phildb/master.svg
    :target: https://travis-ci.org/amacd31/phildb

.. |Appveyor Status| image:: https://img.shields.io/appveyor/ci/amacd31/phildb/master.svg
    :target: https://ci.appveyor.com/project/amacd31/phildb

.. |DOI| image:: https://zenodo.org/badge/14104/amacd31/phildb.svg
    :target: https://zenodo.org/badge/latestdoi/14104/amacd31/phildb

.. |Code Coverage| image:: https://img.shields.io/coveralls/amacd31/phildb/master.svg
    :target: https://coveralls.io/github/amacd31/phildb?branch=master
