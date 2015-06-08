SHELL := /bin/bash
.PHONY: all test sonar docs

all: test docs

docs:
	make -C doc html

venv: build_venv.sh python_requirements
	./build_venv.sh venv
	touch venv

test:
	. load_env; nosetests --cover-erase --with-coverage --cover-package=phildb --cover-html --with-xunit; coverage xml --rcfile=.coveragerc

sonar: test
	sonar-runner -Dsonar.projectVersion=$(shell git describe)
