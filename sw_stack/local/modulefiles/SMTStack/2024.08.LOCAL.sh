#!/bin/bash

# >>>>>>>>>> TOCHANGE <<<<<<<<<<<<<< #
install_dir="/home/fgdeconi/work/sw/stack/src/2024.08.LOCAL/install"
ser_pkgdir="/home/fgdeconi/work/git/serialbox/install"
# >>>>>>>>>>>>>>><<<<<<<<<<<<<< #

# Fix: GT4Py expects CUDA_HOME to be set #
# export CUDA_HOME= $os/etenv("NVHPC_ROOT"), "cuda")

# UCX #
ucx_pkgdir="$install_dir/ucx"
export LD_LIBRARY_PATH="$ucx_pkgdir/lib":$LD_LIBRARY_PATH

# OMPI #
ompi_pkgdir="$install_dir/ompi"

export M_MPI_ROOT=ompi_pkgdir
export OPENMPI=ompi_pkgdir
export MPI_HOME=ompi_pkgdir

export PATH="$ompi_pkgdir/bin":$PATH
export LD_LIBRARY_PATH="$ompi_pkgdir/lib":$LD_LIBRARY_PATH
export INCLUDE="$ompi_pkgdir/include":$INCLUDE
export MANPATH="$ompi_pkgdir/share/man":$MANPATH

export OMPI_MCA_orte_tmpdir_base="/tmp"
export TMPDIR="/tmp"
export OMP_STACKSIZE="1G"
export OMPI_MCA_mca_base_component_show_load_errors="0"
export PMIX_MCA_mca_base_component_show_load_errors="0"

# BOOST HEADERS (as expected by gt4py)
boost_pkgdir="$install_dir/boost"
export BOOST_ROOT= boost_pkgdir

# Baselibs at a BASEDIR #
# >>>>>>>>>> TOCHANGE <<<<<<<<<<<<<< #
# Put down the correct target (linux-gnu, Darwin...)

baselibs_pkgdir="$install_dir/baselibs-7.17.1/install/x86_64-pc-linux-gnu/"
export BASEDIR=baselibs_pkgdir
# >>>>>>>>>><<<<<<<<<<<<<< #

# Serialbox #
export SERIALBOX_ROOT=$ser_pkgdir
export PATH="$ser_pkgdir/python/pp_ser":$PATH
export LD_LIBRARY_PATH="$ser_pkgdir/lib":$LD_LIBRARY_PATH
export PYTHONPATH="$ser_pkgdir/python":$PYTHONPATH

# Python 3
# py_pkgdir="$install_dir/python3"
# export PATH="$py_pkgdir/bin":$PATH
# export LD_LIBRARY_PATH="$py_pkgdir/lib":$LD_LIBRARY_PATH
# export LD_LIBRARY_PATH="$py_pkgdir/lib64":$LD_LIBRARY_PATH
