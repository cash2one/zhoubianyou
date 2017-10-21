#!/bin/bash

BASE_DIR=`pwd`

docker run -d --user $(id -u) -v ${BASE_DIR}/data:/code/data -p "8000:8000" zuobianyou/collector:latest
