#!/bin/bash

HEADER=${1:-${VIRTUI_header:-"Select file"}}
GIVEN_PRESET=${2:-$VIRTUI_preset}
PRESET=${GIVEN_PRESET:-`pwd`"/"}
VIRTUI_prompt= # don't care about prompt

SELECTED=""

true
while [ $? -eq 0 ] && ([ -z $SELECTED ] || ! [ -e $SELECTED ]); do
    SELECTED=`zenity --file-selection --title $HEADER --filename $PRESET 2>/dev/null`
done

SELECTED=${SELECTED:-$GIVEN_PRESET}
echo -n $SELECTED > /dev/stderr
