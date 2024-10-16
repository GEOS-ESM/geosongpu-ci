#!bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

mkdir gnu
cd gnu
git clone https://github.com/SourceryTools/nvptx-tools
git clone git://sourceware.org/git/newlib-cygwin.git nvptx-newlib
git clone --branch releases/gcc-${DSLSW_GNU_VER} git://gcc.gnu.org/git/gcc.git gcc
cd gcc
contrib/download_prerequisites

echo " === GNU gcc/gfortran/g++ with OpenACC and OpenMP Offload on NVIDIA GPUs === "

module rm comp/gcc/12.3.0
module rm nvidia/nvhpc-nompi/23.9
unset CC
unset CXX
unset FC

# Build assembler and linking tools
cd $DSLSW_BASE/gnu/nvptx-tools
./configure \
    --with-cuda-driver-include=$CUDA_DIR/include \
    --with-cuda-driver-lib=$CUDA_DIR/lib64 \
    --prefix=$DSLSW_INSTALL_DIR/gnu
make || exit 1
make install || exit 1
cd ..

# Set up the GCC source tree
cd $DSLSW_BASE/gnu/gcc
ln -s ../nvptx-newlib/newlib newlib
cd ..
export target=$(gcc/config.guess)

# Build nvptx GCC
mkdir build-nvptx-gcc
cd build-nvptx-gcc
../gcc/configure \
    --target=nvptx-none --with-build-time-tools=$DSLSW_INSTALL_DIR/gnu/nvptx-none/bin \
    --enable-as-accelerator-for=$target \
    --disable-sjlj-exceptions \
    --enable-newlib-io-long-long \
    --enable-languages="c,c++,fortran,lto" \
    --prefix=$DSLSW_INSTALL_DIR/gnu
make -j`nproc` || exit 1
make install || exit 1
cd ..

# Build host GCC
mkdir build-host-gcc
cd  build-host-gcc
../gcc/configure \
    --enable-offload-targets=nvptx-none \
    --with-cuda-driver-include=$CUDA_DIR/include \
    --with-cuda-driver-lib=$CUDA_DIR/lib64 \
    --disable-bootstrap \
    --disable-multilib \
    --enable-languages="c,c++,fortran,lto" \
    --prefix=$DSLSW_INSTALL_DIR/gnu
make -j`nproc` || exit 1
make install || exit 1
cd ..