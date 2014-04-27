#!/bin/bash

function pip_install {
    # Not using -r because pip builds before installing and
    # we have dependencies that require the package installed
    # before it can build.
    for requirement in $(cat python_requirements)
    do
          pip install $requirement
    done
}

if [[ ! -d "venv" && $1 -eq "venv" ]]
then
    virtualenv venv
fi

if [[ $1 -eq "venv" ]]
then
(
    . venv/bin/activate
    pip_install
)
elif [[ $1 -eq "" ]]
then
    pip_install
elif [[ ! $1 -eq "" ]]
then
(
    . $1/bin/activate
    pip_install
)
fi
