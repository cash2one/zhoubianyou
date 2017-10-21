#!/bin/bash

docker run -d -v ./data:/code/data -p "8000:8000" zuobianyou/collector:latest
