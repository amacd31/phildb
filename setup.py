import os
from io import open

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'phildb/_version.py'
versioneer.versionfile_build = 'phildb/_version.py'
versioneer.tag_prefix = 'v'
versioneer.parentdir_prefix = 'phildb-'

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = ''.join([
            line for line in f.readlines() if 'travis-ci' not in line
        ])

requirements = [
        "ipython>=2.0.0",
        "numpy>=1.8.0",
        "pandas>=0.14.0",
        "SQLAlchemy>=0.9.2",
        "tables>=3.1.0",
    ]

setup(
    name='PhilDB',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Timeseries database',
    long_description=long_description,
    author='Andrew MacDonald',
    author_email='andrew@maccas.net',
    license='BSD',
    url='https://github.com/amacd31/phildb',
    install_requires=requirements,
    packages = ['phildb'],
    test_suite = 'tests',
    scripts=['bin/phil-create',
            'bin/phil',
        ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
