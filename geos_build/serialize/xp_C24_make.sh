#!/bin/bash

source ./basics.sh

rm -rf $XP_C24
mkdir -p $XP_C24

cd $GEOS_INSTALLDIR/bin
$TBC_SCRIPTS/create_expt.py \
    --horz c24 --vert 72 \
    --nonhydro --nooserver \
    --moist GFDL \
    --link \
    --expdir $XP_BASEDIR \
    $XP_C24_NAME

# Make one day - pre-written script -
cd $XP_C24
$TBC_SCRIPTS/makeoneday.bash

# Make 1x1 layout
sed -e "/^ *NX:/ s/\([0-9]\+\)/1/" AGCM.rc 
sed -e "/^ *NY:/ s/\([0-9][0-9]\+\)/6/" AGCM.rc

# Make 1ts for serialization
sed -e '/^JOB_SGMT:/s/000000[0-9][0-9] 000000/00000000 003001/' CAP.rc

