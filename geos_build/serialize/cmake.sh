#!/bin/bash

source ./basics.sh

rm -rf $GEOS_BUILDIR
mkdir -p $GEOS_BUILDIR
cd $GEOS_BUILDIR
export TMP="$GEOS_BUILDIR/tmp"
export TMPDIR=$TMP
export TEMP=$TMP
mkdir -p $TMP

export FC=mpif90
export CC=mpicc
export CXX=mpic++

cmake .. -DBASEDIR=$BASEDIR/Linux \
         -DCMAKE_Fortran_COMPILER=mpif90 \
         -DBUILD_PYFV3_INTERFACE=OFF \
         -DBUILD_PYMOIST_INTERFACE=OFF \
         -DCMAKE_INSTALL_PREFIX=$GEOS_INSTALLDIR \
         -DPython3_EXECUTABLE=`which python3` \
         -DBUILD_SERIALBOX_SER=ON \
         -DSERIALBOX_ROOT=$SERIALBOX_ROOT \
         -DCMAKE_BUILD_TYPE=Debug
