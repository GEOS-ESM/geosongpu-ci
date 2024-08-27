#!/bin/bash

# Setup tech stack
module use -a /discover/nobackup/projects/geosongpu/sw_sles15/live/modulefiles
module load SMTStack/2024.04.00
# < load virtual environment to get local NDSL/GT4Py/DaCe >

# GEOS Build directory
export GEOS_BASEDIR="/discover/nobackup/fgdeconi/work/git/fp"
export GEOS_BUILDIR="$GEOS_BASEDIR/geos/build_SERIALIZE"
export GEOS_INSTALLDIR="$GEOS_BASEDIR/geos/install_SERIALIZE"

# Experiments
export XP_BASEDIR="/discover/nobackup/fgdeconi/work/git/fp/experiments"
export XP_C24_NAME="TBC_C24_L72"
export XP_C24="$XP_BASEDIR/$XP_C24_NAME"
export TBC_SCRIPTS ="/home/mad/work/TinyBCs-GitV10/scripts/"

# Build details
$BUILD_CORES=48 #how many cores to build
