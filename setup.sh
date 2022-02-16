#!/bin/bash

mkdir -p batch
mkdir -p tmp/jp2 tmp/converted

docker build -t image-converter .