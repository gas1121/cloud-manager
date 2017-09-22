#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/cloudmanager/Dockerfile --tag=gas1121/cloud-manager:cloudmanager-test .

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec cloud-manager nosetests -v --with-coverage --cover-erase
# get coverage data from container
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q cloud-manager):/app/.coverage .
# change path in coverage data
sudo sed -i 's#/app#'"$PWD"'/cloudmanager#g' .coverage
# send coverage report
sudo chown travis:travis .coverage
# send coverage report
pip install coveralls
coveralls

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/cloud-manager:cloudmanager-test
