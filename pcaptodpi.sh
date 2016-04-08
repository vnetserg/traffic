#!/bin/bash

dir=$1
shift $((1))

rm -rf $dir
mkdir -p $dir

rm -rf tmp/dis/
mkdir -p tmp/dis/

echo -n "Launching dissect... "
./dissect.py -d tmp/dis/ $@
echo "OK."

echo -n "Launching dpi... "
./dpi.py -d $dir -mrq tmp/dis/*
echo "OK."

rm -rf tmp/dis/