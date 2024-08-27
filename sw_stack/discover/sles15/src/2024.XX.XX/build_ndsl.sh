#!bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === Make NDSL venv === "

# Git clone `ndsl`, with the minimuum amount of history
cd $DSLSW_INSTALL_DIR
git clone --recurse-submodules --shallow-submodules -b $DSLSW_NDSL_VER --single-branch --depth 1 https://github.com/NOAA-GFDL/NDSL.git ndsl
cd $DSLSW_BASE

cd $DSLSW_INSTALL_DIR
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade setuptools pip
pip install -e $DSLSW_INSTALL_DIR/ndsl
pip install mpi4py cffi cupy-cuda12x
