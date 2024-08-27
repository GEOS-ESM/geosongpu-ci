#!bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === OSU === "

wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz
tar xfp osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz
rm osu-micro-benchmarks-$DSLSW_OSUMICRO_VER.tar.gz

cd $DSLSW_BASE/osu-micro-benchmarks-$DSLSW_OSUMICRO_VER
./configure \
    CC=mpicc \
    CXX=mpicxx \
    --prefix=$DSLSW_INSTALL_DIR/osu \
    --enable-cuda \
    --with-cuda-include=$CUDA_DIR/include \
    --with-cuda=$CUDA_DIR \
    --with-cuda-libpath=$CUDA_DIR/lib64/stubs/

make -j32
make install