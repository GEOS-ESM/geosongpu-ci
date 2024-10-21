#!/bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === Python === "

wget https://www.python.org/ftp/python/$DSLSW_PY_VER/Python-$DSLSW_PY_VER.tgz
tar zxpvf Python-$DSLSW_PY_VER.tgz
rm Python-$DSLSW_PY_VER.tgz

cd $DSLSW_BASE/Python-$DSLSW_PY_VER
./configure --prefix=$DSLSW_INSTALL_DIR/python3 --enable-shared --enable-optimizations

make -j32
make install
