#!/bin/sh

# Source the share basics
source ./basics.v1.0.0.sh

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

wget https://github.com/GridTools/serialbox/archive/refs/tags/v$DSLSW_SERIALBOX_VER.tar.gz
mv v$DSLSW_SERIALBOX_VER.tar.gz serialbox-$DSLSW_SERIALBOX_VER.tar.gz
tar zxpvf serialbox-$DSLSW_SERIALBOX_VER.tar.gz
rm serialbox-$DSLSW_SERIALBOX_VER.tar.gz

git clone --recurse-submodules -b v$DSLSW_BASELIBS_VER https://github.com/GEOS-ESM/ESMA-Baselibs.git ./baselibs/$DSLSW_BASELIBS_VER
cd ./baselibs/$DSLSW_BASELIBS_VER
make download
echo "=>Baselibs >> Removing HDF4 from the ESSENTIALS"
sed -i 's/ESSENTIAL_DIRS = jpeg zlib szlib hdf4 hdf5/ESSENTIAL_DIRS = jpeg zlib szlib hdf5/g' GNUmakefile
sed -i 's/\/zlib \/szlib \/jpeg \/hdf5 \/hdf \/netcdf,\\/\/ \/zlib \/szlib \/jpeg \/hdf5 \/netcdf,\\/g' GNUmakefile
cd $DSLSW_BASE
