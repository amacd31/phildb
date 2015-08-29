PhilDB project
============

Timeseries database project: For storing potentially changing timeseries
data. For example hydrological data, like streamflow data, where the
timeseries may be revised as quality control processes improve the
recorded dataset over time.

PhilDB should be capable of storing data at any frequency supported by
Pandas. At this time only daily data has been extensively tested with
some limited sub-daily usage.

Dependencies
------------

Requires Python 2.7 or greater (mostly tested with Python 2.7 on Mac OSX
and Linux). Test suite status when run with Python 2.7, 3.2 and 3.3 on
Ubuntu (using travis): |Build Status|

All the python dependencies are recorded in the python\_requirements
file.

Installation
------------

PhilDB is pip installable.

The latest stable version can be installed from github with::

    pip install git+https://github.com/amacd31/phildb.git

The latest development version can be installed from github with::

    pip install git+https://github.com/amacd31/phildb.git@dev

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

    phil new_tsdb

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

Located in examples/acorn-sat this example demonstrates loading minimum
and maximum daily temperature records for 112 stations around Australia.

The dataset used in this example is the Australian Climate Observations
Reference Network – Surface Air Temperature (ACORN-SAT) as found on the
Australian Bureau of Meteorology website
`ACORN-SAT <http://www.bom.gov.au/climate/change/acorn-sat/>`__.

BOM Observations
----------------

Located in examples/bom\_observations this example demonstrates loading
half hourly air temperature data from a 72 hour observations JSON file.

The data used in this example is a 72 hour observations JSON file from
the Australian Bureau of Meteorology website (e.g. JSON file as linked
on this page: `Sydney Airport
observations <http://www.bom.gov.au/products/IDN60901/IDN60901.94767.shtml#other_formats>`__

HRS
---

Located in examples/hrs this example demonstrates loading daily
streamflow data for 221 streamflow stations around Australia.

The dataset used in this example is the Hydrologic Reference Stations
(HRS) dataset as found on the Australian Bureau of Meteorology website
`HRS <http://www.bom.gov.au/water/hrs/>`__.

This example also includes a script to calculate the auto-correlation
for all the streamflow timeseries in the HRS dataset.

.. |Build Status| image:: https://travis-ci.org/amacd31/phildb.svg?branch=master
