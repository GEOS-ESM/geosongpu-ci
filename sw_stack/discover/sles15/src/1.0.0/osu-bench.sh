#!/bin/bash

source basics.sh

# need to be ran on a salloc with 2 process on one node each
if [[ $(hostname -s) != warpa* ]]; then
    echo "salloc on a 2 warpa nodes!"
    exit 0
fi

which 'mpirun'
which 'osu_bw'

echo "Host to Host"
mpirun  -x UCX_IB_GPU_DIRECT_RDMA=0 \
        -mca btl '^openib' \
        -mca pml ucx \
        -mca opal_warn_on_missing_libcuda 1 \
        -mca btl_smcuda_cuda_ipc_verbose 1 \
        -mca btl_openib_want_cuda_gdr 1 \
        -mca orte_tmpdir_base $TSE_TMPDIR \
        -mca orte_base_help_aggregate 0 \
        -x UCX_TLS=rc,cuda,cuda_copy,gdr_copy \
        -x UCX_RNDV_THRESH=8192 \
        osu_bw -x 100 -i 100 -d cuda H H

echo "Device: RDMA + GDRCOPY"
mpirun  -x UCX_IB_GPU_DIRECT_RDMA=1 \
        -x UCX_RNDV_SCHEME=get_zcopy \
        -x UCX_MEMTYPE_CACHE=n \
        -x UCX_RNDV_THRESH=8192 \
        -x UCX_TLS=rc,cuda,cuda_copy,gdr_copy \
        -mca pml ucx \
        -mca opal_warn_on_missing_libcuda 1 \
        -mca btl_smcuda_cuda_ipc_verbose 1 \
        -mca btl_openib_want_cuda_gdr 1 \
        -mca orte_tmpdir_base $TSE_TMPDIR \
        -mca orte_base_help_aggregate 0 \
        -mca btl '^openib' \
        osu_bw -x 100 -i 100 -d cuda D D

echo "Device: RDMA only"
mpirun  -x UCX_IB_GPU_DIRECT_RDMA=1 \
        -x UCX_RNDV_SCHEME=get_zcopy \
        -x UCX_MEMTYPE_CACHE=n \
        -x UCX_RNDV_THRESH=8192 \
        -x UCX_TLS=rc,cuda,cuda_copy \
        -mca pml ucx \
        -mca opal_warn_on_missing_libcuda 1 \
        -mca btl_smcuda_cuda_ipc_verbose 1 \
        -mca btl_openib_want_cuda_gdr 1 \
        -mca orte_tmpdir_base $TSE_TMPDIR \
        -mca orte_base_help_aggregate 0 \
        -mca btl '^openib' \
        osu_bw -x 100 -i 100 -d cuda D D

echo "Device: GDR_COPY only"
mpirun  -x UCX_IB_GPU_DIRECT_RDMA=0 \
        -x UCX_RNDV_SCHEME=get_zcopy \
        -x UCX_MEMTYPE_CACHE=n \
        -x UCX_RNDV_THRESH=8192 \
        -x UCX_TLS=rc,cuda,cuda_copy,gdr_copy \
        -mca pml ucx \
        -mca opal_warn_on_missing_libcuda 1 \
        -mca btl_smcuda_cuda_ipc_verbose 1 \
        -mca btl_openib_want_cuda_gdr 1 \
        -mca orte_tmpdir_base $TSE_TMPDIR \
        -mca orte_base_help_aggregate 0 \
        -mca btl '^openib' \
        osu_bw -x 10i -i 10 -d cuda D D


echo "Device: default"
mpirun  -x UCX_IB_GPU_DIRECT_RDMA=0 \
        -x UCX_RNDV_SCHEME=get_zcopy \
        -x UCX_MEMTYPE_CACHE=n \
        -x UCX_RNDV_THRESH=8192 \
        -x UCX_TLS=rc,cuda,cuda_copy \
        -mca pml ucx \
        -mca opal_warn_on_missing_libcuda 1 \
        -mca btl_smcuda_cuda_ipc_verbose 1 \
        -mca btl_openib_want_cuda_gdr 1 \
        -mca orte_tmpdir_base $TSE_TMPDIR \
        -mca orte_base_help_aggregate 0 \
        -mca btl '^openib' \
        osu_bw -x 10 -i 10 -d cuda D D
