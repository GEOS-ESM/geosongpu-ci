""" Access K as an absolute index, while retaining I/J as relative index and output to 2D.

Last update: 2024/07/25
Description: gt4py doesn't allow for direct indexing in K while doing relative indexing in the
    other cartesian dimensions. We use a masking technique in stencil to copy the relative data.
    Additionally a 2D output means we are barred to use PARALLEL and have to use FORWARD (a potential harsh limiter)
    WARNING: this code returns O as a 2D Field
Fortran equivalent:
```fortran
do L=1,LM
  do J=1,JM
   do I=1,IM
      ...
      PLmb(i,j, KLCL(I,J))
      ...
```
as seen in https://github.com/GEOS-ESM/GEOSgcm_GridComp/blob/db55c301840d98b788b0e17045510af726c0f555/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/GEOS_GFDL_1M_InterfaceMod.F90#L589
"""

from gt4py.cartesian.gtscript import computation, interval, FORWARD
from ndsl.boilerplate import get_factories_single_tile_numpy
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl.dsl.typing import FloatField, FloatFieldIJ, IntFieldIJ, IntField
from ndsl import StencilFactory, QuantityFactory, orchestrate
import numpy as np

domain = (3, 3, 4)
nhalo = 0
stcil_fctry, ijk_qty_fctry = get_factories_single_tile_numpy(
    domain[0], domain[1], domain[2], nhalo
)


def stencil(
    data_field: FloatField,
    k_mask: FloatField,
    k_index_desired: FloatFieldIJ,
    out_field: FloatFieldIJ,
):
    with computation(FORWARD), interval(...):
        if k_mask == k_index_desired:
            out_field = data_field


class Code:
    def __init__(
        self,
        stencil_factory: StencilFactory,
        qty_fctry: QuantityFactory,
    ):
        orchestrate(obj=self, config=stencil_factory.config.dace_config)
        self.stencil = stcil_fctry.from_dims_halo(
            func=stencil,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )
        self.O = qty_fctry.zeros([X_DIM, Y_DIM], "n/a")

    def __call__(
        self,
        # out_field: FloatField,
        k_mask: IntField,
        k_index_desired: IntFieldIJ,
        data_field: IntField,
    ):
        self.stencil(data_field, k_mask, k_index_desired, self.O)


if __name__ == "__main__":
    k_mask = ijk_qty_fctry.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")

    k_index_desired = ijk_qty_fctry.zeros([X_DIM, Y_DIM], "n/a")
    k_index_desired.view[:, :] = np.random.randint(
        0, domain[2], size=(domain[0], domain[1])
    )

    input_to_sample_from = ijk_qty_fctry.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    input_to_sample_from.view[:, :, :] = np.random.randint(800, 900, size=domain)

    for i in range(0, domain[0]):
        for j in range(0, domain[1]):
            for k in range(0, domain[2]):
                k_mask.view[i, j, k] = k

    code = Code(stcil_fctry, ijk_qty_fctry)
    code(k_mask, k_index_desired, input_to_sample_from)

    print(f"Mask:\n{k_mask.view[:,:,:]}\n")
    print(f"K Level Desired for each column:\n{k_index_desired.view[:,:]}\n")
    print(f"Input to sample from:\n{input_to_sample_from.view[:,:,:]}\n")
    print(f"Output:\n{code.O.view[:,:]}\n")
