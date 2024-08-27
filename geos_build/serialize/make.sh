#!/bin/bash

source ./basics.sh


cd $GEOS_BUILDIR

export TMP="$GEOS_BUILDIR/tmp"
export TMPDIR=$TMP
export TEMP=$TMP

make -j$BUILD_CORES install
