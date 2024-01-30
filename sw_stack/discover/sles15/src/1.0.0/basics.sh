#!/bin/bash

export DSLSW_VERSION="1.0.0"
echo "DSL Software Stack v${DSLSW_VERSION}"

# Version
export DSLSW_GDRCOPY_VER=2.3
export DSLSW_OMPI_MAJOR_VER=4.1
export DSLSW_OMPI_VER=${DSLSW_OMPI_MAJOR_VER}.6
export DSLSW_UCX_VER=1.15.0
export DSLSW_CUDA_VER=12.2
export DSLSW_OSUMICRO_VER=7.3
export DSLSW_LAPACK_VER=3.11.0
export DSLSW_PY_VER=3.8.10
export DSLSW_BASELIBS_VER=7.14.1
export DSLSW_SERIALBOX_VER=2.6.1
export DSLSW_GNU_VER=12.2.0

# Base directory & versioning
export DSLSW_BASE=$PWD/build
mkdir -p $DSLSW_BASE
export DSLSW_INSTALL_DIR=$PWD/install
mkdir -p $DSLSW_INSTALL_DIR

# Modules
module load nvidia/nvhpc-nompi/23.9
CUDA_DIR=/usr/local/other/nvidia/hpc_sdk/Linux_x86_64/23.9/cuda/
module load comp/gcc/12.3.0
module load other/boost/1.77.0
module use -a /discover/nobackup/projects/geosongpu/sw_sles15/modulesfiles/
module load DSLwork/1.0.0

# Enforce proper compilers
export FC=gfortran
export CC=gcc
export CXX=g++

echo "TODO: make modules!" # once we have modules this isn't required a module load (if available) will be enough
export LD_LIBRARY_PATH=$DSLSW_INSTALL_DIR/ompi/lib:$DSLSW_INSTALL_DIR/ucx/lib:$DSLSW_INSTALL_DIR/python3/lib:$LD_LIBRARY_PATH
export PATH=$DSLSW_INSTALL_DIR/ompi/bin:$DSLSW_INSTALL_DIR/python3/bin:$PATH:$DSLSW_INSTALL_DIR/osu/libexec/osu-micro-benchmarks/mpi/pt2pt/

