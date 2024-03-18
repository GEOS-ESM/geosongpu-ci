#!/bin/bash

# Source the shared basics
source ./basics.sh

echo " === GDR Copy (requires kernel running on the box) === "
#cd $DSLSW_BASE/gdrcopy-$DSLSW_GDRCOPY_VER
#make prefix=$DSLSW_INSTALL_DIR/gdrcopy CUDA=$CUDA_DIR all install
#exit 0

echo " === UCX === "
cd $DSLSW_BASE/ucx-$DSLSW_UCX_VER
./configure --prefix=$DSLSW_INSTALL_DIR/ucx \
            --enable-optimizations \
            --disable-logging \
            --disable-debug \
            --disable-assertions \
            --disable-params-check \
            --without-xpmem \
            --without-java \
            --without-go \
            --with-cuda=$CUDA_DIR \
            --with-gdrcopy=/usr/src/gdrdrv-$DSLSW_GDRCOPY_VER/

make -j 32 install
#exit 0

echo " === OpenMPI === "

# NSL lib (-lnsl) was not symlink from libnsl.so.1 which lead to issues (--disable-getpwuid is an attempt to squash that, which seems unsucessful). Potentially, removing the LSF scheduler build would work.

# libxml2 has a /zero on it's init (https://gitlab.gnome.org/GNOME/libxml2/-/blob/7846b0a677f8d3ce72486125fa281e92ac9970e8/xpath.c#L505) which seems to trigger a sigfpe. Relying on the internal but potentially wobly XML parser of OMPI

cd $DSLSW_BASE/openmpi-${DSLSW_OMPI_VER}
./configure --prefix=$DSLSW_INSTALL_DIR/ompi \
            --disable-libxml2 \
            --disable-wrapper-rpath \
            --disable-wrapper-runpath \
            --with-pmix \
            --with-cuda=$CUDA_DIR \
            --with-cuda-libdir=$CUDA_DIR/lib64/stubs \
            --with-ucx=$DSLSW_INSTALL_DIR/ucx \
            --with-slurm \
            --enable-mpi1-compatibility

make -j32 all 
make install 
export PATH=$DSLSW_INSTALL_DIR/ompi/bin:$PATH
export LD_LIBRARY_PATH=$DSLSW_INSTALL_DIR/ompi/lib:$DSLSW_INSTALL_DIR/ucx/lib:$LD_LIBRARY_PATH

echo " === OSU === "

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

echo " === Lapack === "
cd $DSLSW_BASE/lapack-$DSLSW_LAPACK_VER
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$DSLSW_INSTALL_DIR/lapack
make -j32 install

echo " === Python === "
cd $DSLSW_BASE/Python-$DSLSW_PY_VER
./configure --prefix=$DSLSW_INSTALL_DIR/python3 --enable-shared --enable-optimizations

make -j32
make install

echo " === Serialbox === "
cd $DSLSW_BASE/serialbox-$DSLSW_SERIALBOX_VER
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$DSLSW_INSTALL_DIR/serialbox \
      -DSERIALBOX_ENABLE_FORTRAN=ON \
      -DSERIALBOX_EXAMPLES=OFF \
      ..
make -j32 install


echo " === Baselibs === "
make ESMF_COMM=openmpi BUILD=ESSENTIALS ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch --prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/x86_64-pc-linux-gnu/Linux install

if [ -z ${BUILD_GCC_OFFLOAD+x} ]; then
    echo "Skip building offloaded GCC. Define BUILD_GCC_OFFLOAD to build."
else
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
fi

echo " === Make NDSL venv === "
cd $DSLSW_INSTALL_DIR
./python3/bin/python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade setuptools pip
pip install -e $DSLSW_INSTALL_DIR/ndsl
