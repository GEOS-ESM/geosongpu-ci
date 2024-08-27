#!bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

# Stream include out of boost source
cd $DSLSW_INSTALL_DIR
wget https://boostorg.jfrog.io/artifactory/main/release/$DSLSW_BOOST_VER/source/boost_$DSLSW_BOOST_VER_STR.tar.gz
tar zxpvf boost_$DSLSW_BOOST_VER_STR.tar.gz
rm boost_$DSLSW_BOOST_VER_STR.tar.gz
mkdir -p boost/include
mv boost_$DSLSW_BOOST_VER_STR/boost boost/include
rm -r boost_$DSLSW_BOOST_VER_STR
cd $DSLSW_BASE