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

rm -rf tmp/sorted/
mkdir -p tmp/sorted/

echo -n "Launching grab... "
./grab.py $1 -t tmp/sorted/ $all
echo "OK."

echo -n "Launching forge... "
./forge.py tmp/sorted/ -o $outfile -s $strip
echo "OK."

echo "Result written to '$outfile'"

rm -rf tmp/sorted/