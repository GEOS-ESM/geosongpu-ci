#!/bin/bash

source ./basics.sh

cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
make ESMF_COMM=openmpi \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/x86_64-pc-linux-gnu/Linux \
    verify
