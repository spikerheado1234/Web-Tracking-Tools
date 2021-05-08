#! /bin/bash

docker build -t influx .;
docker run -d -p 8086:80086 influx;
