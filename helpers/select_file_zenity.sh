#!/bin/bash

HEADER=${1:-${VIRTUI_header:-"Select file"}}
PRESET=${2:-${VIRTUI_preset:-`pwd`"/"}}
VIRTUI_prompt= # don't care about prompt

SELECTED=""

true
while [ $? -eq 0 ] && ([ -z $SELECTED ] || ! [ -e $SELECTED ]); do
    SELECTED=`zenity --file-selection --title $HEADER --filename $PRESET`
done
echo -n $SELECTED > /dev/stderr
