#!/bin/bash

dir=$1
shift $((1))

rm -rf $dir
mkdir -p $dir

rm -rf /tmp/traffic/dis
mkdir -p /tmp/traffic/dis

echo -n "Launching dissect... "
./dissect.py -d /tmp/traffic/dis $@
echo "OK."

echo -n "Launching dpi... "
./dpi.py -d $dir -mrq /tmp/traffic/dis/*
echo "OK."

rm -rf /tmp/traffic/dis