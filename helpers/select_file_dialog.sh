#!/bin/bash

VIRTUI_header= # don't care about header
GIVEN_PRESET=${2:-$VIRTUI_preset}
PRESET=${GIVEN_PRESET:-`pwd`"/"}
VIRTUI_prompt= # don't care about prompt

SELECTED=""

TMPFILE=`mktemp`

RETCODE=0
while [ $RETCODE -eq 0 ] && ([ -z $SELECTED ] || ! [ -e $SELECTED ]); do
    dialog --fselect $PRESET 25 80 2> $TMPFILE
    RETCODE=$?
    SELECTED=`cat $TMPFILE`
done

SELECTED=${SELECTED:-$GIVEN_PRESET}
echo -n $SELECTED > /dev/stderr
