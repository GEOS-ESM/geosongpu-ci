#!/bin/bash

source ./basics.v1.0.0.sh

cd $DSLSW_BASE
git clone --recurse-submodules -b v$DSLSW_BASELIBS_VER https://github.com/GEOS-ESM/ESMA-Baselibs.git ./baselibs/$DSLSW_BASELIBS_VER
cd ./baselibs/$DSLSW_BASELIBS_VER
make download
echo "=>Baselibs >> Removing HDF4 from the ESSENTIALS"
sed -i 's/ESSENTIAL_DIRS = jpeg zlib szlib hdf4 hdf5/ESSENTIAL_DIRS = jpeg zlib szlib hdf5/g' GNUmakefile
sed -i 's/\/zlib \/szlib \/jpeg \/hdf5 \/hdf \/netcdf,\\/\/ \/zlib \/szlib \/jpeg \/hdf5 \/netcdf,\\/g' GNUmakefile
cd $DSLSW_BASE

