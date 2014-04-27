#!/bin/bash

function pip_install {
    which python
    python --version
    # Not using -r because pip builds before installing and
    # we have dependencies that require the package installed
    # before it can build.
    for requirement in $(cat python_requirements)
    do
          pip install $requirement
    done
}

if [ ! -d "venv" ] && [ "x$1" = "xvenv" ]
then
    virtualenv venv
fi

if [[ $1 = "venv" ]]
then
(
    . venv/bin/activate
    pip_install
)
elif [[ "x$1" = "x" ]]
then
    pip_install
elif [[ ! "x$1" = "x" ]]
then
(
    . $1/bin/activate
    pip_install
)
fi
