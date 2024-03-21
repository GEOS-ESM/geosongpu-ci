#!/bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

# GDR Copy should be present in /usr/src/gdrdrv-*
#wget -c https://github.com/NVIDIA/gdrcopy/archive/refs/tags/v$DSLSW_GDRCOPY_VER.tar.gz
#tar zxpvf v$DSLSW_GDRCOPY_VER.tar.gz
#rm v$DSLSW_GDRCOPY_VER.tar.gz

wget https://github.com/openucx/ucx/releases/download/v${DSLSW_UCX_VER}/ucx-${DSLSW_UCX_VER}.tar.gz
tar xfp ucx-$DSLSW_UCX_VER.tar.gz
rm ucx-$DSLSW_UCX_VER.tar.gz

wget https://download.open-mpi.org/release/open-mpi/v$DSLSW_OMPI_MAJOR_VER/openmpi-${DSLSW_OMPI_VER}.tar.gz
tar xfzp openmpi-$DSLSW_OMPI_VER.tar.gz
rm openmpi-$DSLSW_OMPI_VER.tar.gz

wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz
tar xfp osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz
rm osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz

wget https://github.com/Reference-LAPACK/lapack/archive/refs/tags/v$DSLSW_LAPACK_VER.tar.gz
tar xfzp v$DSLSW_LAPACK_VER.tar.gz
rm v$DSLSW_LAPACK_VER.tar.gz

wget https://www.python.org/ftp/python/$DSLSW_PY_VER/Python-$DSLSW_PY_VER.tgz
tar zxpvf Python-$DSLSW_PY_VER.tgz
rm Python-$DSLSW_PY_VER.tgz

git clone https://github.com/GridTools/serialbox.git serialbox-$DSLSW_SERIALBOX_VER
cd serialbox-$DSLSW_SERIALBOX_VER
git checkout $DSLSW_SERIALBOX_SHA
cd $DSLSW_BASE

git clone --recurse-submodules -b v$DSLSW_BASELIBS_VER https://github.com/GEOS-ESM/ESMA-Baselibs.git ./baselibs-$DSLSW_BASELIBS_VER
cd ./baselibs-$DSLSW_BASELIBS_VER
make download
echo "=>Baselibs >> Removing HDF4 from the ESSENTIALS"
sed -i 's/ESSENTIAL_DIRS = jpeg zlib szlib hdf4 hdf5/ESSENTIAL_DIRS = jpeg zlib szlib hdf5/g' GNUmakefile
sed -i 's/\/zlib \/szlib \/jpeg \/hdf5 \/hdf \/netcdf,\\/\/ \/zlib \/szlib \/jpeg \/hdf5 \/netcdf,\\/g' GNUmakefile
cd $DSLSW_BASE

if [ -z ${BUILD_GCC_OFFLOAD+x} ]; then
    echo "Skip building offloaded GCC. Define BUILD_GCC_OFFLOAD to build."
else
    mkdir gnu
    cd gnu
    git clone https://github.com/SourceryTools/nvptx-tools
    git clone git://sourceware.org/git/newlib-cygwin.git nvptx-newlib
    git clone --branch releases/gcc-${DSLSW_GNU_VER} git://gcc.gnu.org/git/gcc.git gcc
    cd gcc
    contrib/download_prerequisites
fi

# Stream include out of boost source
cd $DSLSW_INSTALL_DIR
wget https://boostorg.jfrog.io/artifactory/main/release/$DSLSW_BOOST_VER/source/boost_$DSLSW_BOOST_VER_STR.tar.gz
tar zxpvf boost_$DSLSW_BOOST_VER_STR.tar.gz
rm boost_$DSLSW_BOOST_VER_STR.tar.gz
mkdir -p boost/include
mv boost_$DSLSW_BOOST_VER_STR/boost boost/include
rm -r boost_$DSLSW_BOOST_VER_STR
cd $DSLSW_BASE

# Git clone `ndsl`, with the minimuum amount of history
cd $DSLSW_INSTALL_DIR
git clone --recurse-submodules --shallow-submodules -b $DSLSW_NDSL_VER --single-branch --depth 1 https://github.com/NOAA-GFDL/NDSL.git ndsl
cd $DSLSW_BASE
