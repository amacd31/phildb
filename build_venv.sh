#!/bin/bash

if [[ ! -d "venv" ]]
then
    virtualenv venv
fi

(
    . venv/bin/activate
    # Not using -r because pip builds before installing and
    # we have dependencies that require the package installed
    # before it can build.
    for requirement in $(cat python_requirements)
    do
          pip install $requirement
    done
)
