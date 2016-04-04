#!/bin/bash

strip=0
outfile='flows.csv'
all=''

while getopts ":o:s:a" opt; do
    case $opt in
    o) outfile=$OPTARG ;;
    s) strip=$OPTARG ;;
    a) all="-a" ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
    esac
    shift $((OPTIND-1))
    OPTIND=0
done

./pcaptodpi.sh /tmp/traffic/dpi $@
./dpitocsv.sh -o $outfile -s $strip $all /tmp/traffic/dpi

rm -rf /tmp/traffic/dpi