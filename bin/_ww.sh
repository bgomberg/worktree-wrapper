#!/usr/bin/bash

TEMPFILE="$HOME/.wwtmp"

if [ -f $TEMPFILE ]; then
    rm $TEMPFILE
fi

_ww_helper.py "$@"

if [ -f $TEMPFILE ]; then
    source $TEMPFILE
    rm $TEMPFILE
fi
