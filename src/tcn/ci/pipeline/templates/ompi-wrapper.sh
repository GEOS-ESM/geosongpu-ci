# Turn MPS on
export MPS_ON=1

# Read `np`
NP="$2"
shift
shift

# Forward to the launcher
mpirun -np $NP ./gpu-mps-launcher.sh $*
