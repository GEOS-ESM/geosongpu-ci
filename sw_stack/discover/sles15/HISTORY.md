# GPU-accelerated software stack for GEOS

## Methodology

All versions of the software for a given version are saved in `basics.sh`.
`build` directory is the throwaway directory where everything is downloaded then built.
`install` is saves all library and executable once build is done.

Last edit: _December 29th 2023_

## v1.0.0

### OpenMPI

We build OpenMPI throught the UCX layer with cuda-enabled and GRDCopy and GPUDirect on (linus kernels are check via `check_gpu_comms`).

- GDRCOPY: 2.3
- GCC: 12.3.0 [^1] (via `comp/gcc/12.3.0` on discover)
- CUDA (via `nvhpc`): 12.2 [^2] (via `nvidia/nvhpc-nompi/23.9` on discover)
- UCX: 1.15.0
- OpenMPI: 4.1.6 [^3]
- OSU-MICROBENCHMARK: 7.2

Test of the stack can be done via the `osu-microbenchmark` with latency & bandwith saved in `osu-bench.sh`.

_Note:_

- [^1]: `gcc-13.2.0` fails during GEOS with an internal compiler error
- [^2]: `nvhpc` ships with a prebuilt `openmpi` which can cause issues. Make sure to load the `nompi` module.
- [^3]: `openmpi-5.0.0` fails at GEOS runtime on a call to `libxml2` that does a divide by zero (triggering a sigfpe). We revert to `4.1.6`.

### Baselibs

- LAPACK/BLAS: 3.11.0
- BASELIBS: 7.14.1

### Python

- Python: 3.8.10 [^4]

### Serialbox

- Latest stable is 2.6.1. Development is over.

_Note:_

- [^4]: `3.10.12` leads to failure in DaCe parsing.
