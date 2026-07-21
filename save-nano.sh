#! /bin/sh

( sleep 17 ; echo quit ; sleep 2 ) | python3 main.py -s -v -a -ci -x -d tcp://spectra:8234 test-r5f8-spec.csv

