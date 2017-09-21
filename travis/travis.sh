#!/bin/bash

set -e

# test cloudmanager only
cd cloudmanager
# install dependency
pip install -r requirements.txt

# run tests
nosetests -v --with-coverage --cover-erase
if [ $? -eq 1 ]; then
    echo "unit tests failed"
    exit 1
fi

# send coverage report
sudo chown travis:travis .coverage
coveralls
