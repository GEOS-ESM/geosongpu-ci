#!bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === Serialbox === "

git clone https://github.com/GridTools/serialbox.git serialbox-$DSLSW_SERIALBOX_VER
cd serialbox-$DSLSW_SERIALBOX_VER
git checkout $DSLSW_SERIALBOX_SHA
cd $DSLSW_BASE

cd $DSLSW_BASE/serialbox-$DSLSW_SERIALBOX_VER
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$DSLSW_INSTALL_DIR/serialbox \
    -DSERIALBOX_ENABLE_FORTRAN=ON \
    -DSERIALBOX_EXAMPLES=OFF \
    ..
make -j32 install
