#!/bin/bash

# Source the shared basics
source ./basics.sh

echo " === Make NDSL venv === "
cd $DSLSW_INSTALL_DIR
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade setuptools pip
pip install -e $DSLSW_INSTALL_DIR/ndsl
pip install mpi4py cffi cupy-cuda12x
