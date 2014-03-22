.PHONY: all test sonar

all: test

venv: build_venv.sh python_requirements
	./build_venv.sh
	touch venv

test:
	nosetests --cover-erase --with-coverage --cover-package=tsdb --cover-html --with-xunit; coverage xml --rcfile=.coveragerc

sonar: test
	sonar-runner -Dsonar.projectVersion=$(shell git describe)
