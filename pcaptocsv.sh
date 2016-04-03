#!/bin/bash

strip=0
outfile='flows.csv'

while getopts ":o:s:" opt; do
    case $opt in
    o) outfile=$OPTARG ;;
    s) strip=$OPTARG ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
    esac
    shift $((OPTIND-1))
    OPTIND=0
done

mkdir -p /tmp/traffic/dis
mkdir /tmp/traffic/dpi
mkdir /tmp/traffic/sorted

echo -n "Launching dissect... "
./dissect.py -d /tmp/traffic/dis $@
echo "OK."

echo -n "Launching dpi... "
./dpi.py -d /tmp/traffic/dpi -mrq /tmp/traffic/dis/*
echo "OK."

echo -n "Launching grab... "
./grab.py /tmp/traffic/dpi -t /tmp/traffic/sorted
echo "OK."

echo -n "Launching forge... "
./forge.py /tmp/traffic/sorted -o $outfile -s $strip
echo "OK."

echo "Result written to '$outfile'"

rm -rf /tmp/traffic