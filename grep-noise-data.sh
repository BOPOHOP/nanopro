#! /bin/sh

egrep 'remark, noise:' `ls -1rt thermo-*csv` | sed -e 's/^.*level //;s/ .*-V/ /;s/T//;s/;.*//' | awk ' { printf    "%s %.1f %s%+.3f\n", $3, $1+$2, $2, $1 }'

