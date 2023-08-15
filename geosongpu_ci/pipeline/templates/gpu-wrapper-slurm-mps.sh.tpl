#!/bin/sh

# We open GPU visibility to full node at first
export CUDA_VISIBLE_DEVICES=0,1,2,3

# Hardware sampling is a python tools that reads at intervals
# various hardware sensors (power, usage, memory load...)
if [ -z ${HARDWARE_SAMPLING} ]; then
    echo "Hardware sampling is OFF"
else
    echo "Hardware sampling is ON"
    # We restrict usage to (world) rank 0
    if [ $SLURM_PROCID -eq 0 ]; then
        geosongpu_hws server &
        sleep 10
        geosongpu_hws client start
    fi

fi

if [ -z ${MPS_ON} ]; then
    echo "MPS is OFF"
    # No MPS, we assume rank==GPU
    GPU=$SLURM_LOCALID
    export CUDA_VISIBLE_DEVICES=$GPU
else
    echo "MPS is ON"
    if [ -z ${PER_DEVICE_PROCESS} ]; then
        echo "PER_DEVICE_PROCESS needs to be setup on MPS. Exiting."
        exit 1
    fi
    # All ranks needs to know where to look
    export CUDA_MPS_PIPE_DIRECTORY=./nvidia-mps/$SLURM_NODEID
    export CUDA_MPS_LOG_DIRECTORY=./nvidia-log/$SLURM_NODEID
    # Only 1 rank per node (local rank 0) handles the server chatter
    if [ $SLURM_LOCALID -eq 0 ]; then
        echo "Turn nvidia-cuda-mps-control on for node $SLURM_NODEID"
        mkdir -p nvidia-mps
        mkdir -p nvidia-log/$SLURM_NODEID
        # sudo nividia -i 0 -c 3 # Per docs, we should insure GPU is in EXCLUSIVE mode but we might be curtail by HPC settings
        nvidia-cuda-mps-control -d
    fi
    # MPS server is socket base, leave time for the filesystem
    sleep 10
    # Server should be spun, we restrict this rank to a single GPU
    GPU=$((SLURM_LOCALID/PER_DEVICE_PROCESS))
    export CUDA_VISIBLE_DEVICES=$GPU
fi


echo "Node: $SLURM_NODEID | Rank: $SLURM_PROCID, pinned to GPU: $CUDA_VISIBLE_DEVICES"

# Run program with or without log dump in file
if [ -z ${LOCAL_REDIRECT_LOG} ]; then
    $* > log.redirect_local.%t.out > 2&1
else
    $*
fi

# Clean up of all tools
if [ -z ${HARDWARE_SAMPLING} ]; then
    echo ""
else 
    if [ $SLURM_PROCID -eq 0 ]; then
        geosongpu_hws client dump
        geosongpu_hws client stop
    fi
fi
if [ -z ${MPS_ON} ]; then
    echo ""
else 
    if [ $SLURM_LOCALID -eq 0 ]; then
        echo quit | nvidia-cuda-mps-control
        # sudo nividia -i 0 -c 0 # Per docs, we should insure GPU is flipped back to DEFAULT mode but we might be curtail by HPC settings
    fi
fi
