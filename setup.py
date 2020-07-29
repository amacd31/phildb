import os
from io import open

import versioneer

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "ipython>=2.0.0",
    "numpy>=1.8.0",
    "pandas>=0.24.2",
    "SQLAlchemy>=0.9.2",
    "tables>=3.1.0",
]

setup(
    name="PhilDB",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Timeseries database",
    long_description=long_description,
    author="Andrew MacDonald",
    author_email="andrew@maccas.net",
    license="BSD",
    url="https://github.com/amacd31/phildb",
    install_requires=requirements,
    packages=["phildb"],
    test_suite="nose.collector",
    tests_require=["nose", "mock"],
    entry_points={
        "console_scripts": [
            "phil-create = phildb.create:main",
            "phildb = phildb.console:main",
            "phil = phildb.console:deprecated_main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
