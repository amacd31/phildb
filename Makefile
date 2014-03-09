all:

test:
	nosetests --cover-erase --with-coverage --cover-package=tsdb --cover-html
