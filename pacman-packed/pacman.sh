#!/bin/bash

FULLPATH="$( readlink -f $0 )"
SCRIPTDIR="$( dirname ${FULLPATH} )"
LIBDIR="$( dirname ${SCRIPTDIR} )/lib"
$LIBDIR/loader --library-path $LIBDIR $LIBDIR/pacman $*
