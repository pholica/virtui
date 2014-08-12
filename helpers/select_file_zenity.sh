#!/bin/bash

DIR=${1:-`pwd`}

SELECTED=""

true
while [ $? -eq 0 ] && ([ -z $SELECTED ] || ! [ -e $SELECTED ]); do
    SELECTED=`zenity --file-selection --filename $DIR`
done
echo -n $SELECTED > /dev/stderr
