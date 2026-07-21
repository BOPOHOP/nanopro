#! /bin/sh

( sleep 17 ; echo quit ; sleep 2 ) | python3 main.py -s -v -a -ci -x -d tcp://gs-8000:8234 test-gs-spec.csv

