#!/bin/bash


# >>>>>>>> CHOOSE ONE <<<<<<<<< #

# Modules 
# module use -a /home/fgdeconi/work/sw/stack/modulefiles/
# module load SMTStack/${DSLSW_VERSION}

# Bash source
source /Users/ckropiew/SMT-Nebulae/sw_stack/local/modulefiles/SMTStack/2024.08.LOCAL.sh

# >>>>>>>>>>>>>>><<<<<<<<<<<<<< #

export DSLSW_VERSION="2024.08.LOCAL"
echo "DSL Software Stack v${DSLSW_VERSION}"

# Version
export DSLSW_GDRCOPY_VER=2.3
export DSLSW_OMPI_MAJOR_VER=5.0
export DSLSW_OMPI_VER=${DSLSW_OMPI_MAJOR_VER}.5
export DSLSW_UCX_VER=1.15.0
export DSLSW_CUDA_VER=12.2
export DSLSW_OSUMICRO_VER=7.3
export DSLSW_LAPACK_VER=3.11.0
export DSLSW_PY_VER=3.11.7
export DSLSW_BASELIBS_VER=7.27.0
export DSLSW_SERIALBOX_VER=origin/feature/data_ijkbuff
export DSLSW_GNU_VER=12.2.0
export DSLSW_BOOST_VER=1.76.0
export DSLSW_BOOST_VER_STR=1_76_0 

# Base directory & versioning
export DSLSW_BASE=/Users/ckropiew/SMT-Nebulae/sw_stack/local/src/build
mkdir -p $DSLSW_BASE
export DSLSW_INSTALL_DIR=$install_dir
mkdir -p $DSLSW_INSTALL_DIR

# CUDA
CUDA_DIR=$NVHPC_ROOT/cuda/
