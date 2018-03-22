#!/usr/bin/bash

TEMPFILE="$HOME/.wwtmp"

if [ -f $TEMPFILE ]; then
    rm -f $TEMPFILE
fi

_ww_helper.py "$@"

if [ -f $TEMPFILE ]; then
    source $TEMPFILE
    rm -f $TEMPFILE
fi
