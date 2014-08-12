#!/bin/bash

DIR=${1:-`pwd`}

SELECTED=""

TMPFILE=`mktemp`

RETCODE=0
while [ $RETCODE -eq 0 ] && ([ -z $SELECTED ] || ! [ -e $SELECTED ]); do
    dialog --fselect ./ 25 80 2> $TMPFILE
    RETCODE=$?
    SELECTED=`cat $TMPFILE`
done
echo -n $SELECTED > /dev/stderr
