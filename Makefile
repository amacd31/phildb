.PHONY: all test sonar

all: test

test:
	nosetests --cover-erase --with-coverage --cover-package=tsdb --cover-html --with-xunit; coverage xml --rcfile=.coveragerc

sonar: test
	sonar-runner -Dsonar.projectVersion=$(shell git describe)
