""" Get the top/bottom of the column of air in a stencil

Last update: 2024/07/24
Description: gt4py doesn't allow for direct indexing in K while doing relative indexing in the
    other cartesian dimensions. To be able to get the top/bottom of the column of air, we can
    rely on the `interval` and `temporary` generation features.
Fortran equivalent:
```fortran
do L=1,LM
  do J=1,JM
   do I=1,IM
      ...
      Field(i,j,LM)
      ...
```
as seen in  https://github.com/GEOS-ESM/GEOSgcm_GridComp/blob/db55c301840d98b788b0e17045510af726c0f555/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/GEOS_GFDL_1M_InterfaceMod.F90#L603
"""

from gt4py.cartesian.gtscript import computation, interval, PARALLEL, FORWARD
from ndsl.boilerplate import get_factories_single_tile_orchestrated_cpu
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl.dsl.typing import FloatField, FloatFieldIJ
from ndsl import StencilFactory, QuantityFactory, orchestrate
import numpy as np

domain = (3, 3, 4)

stcil_fctry, ijk_qty_fctry = get_factories_single_tile_orchestrated_cpu(
    domain[0], domain[1], domain[2], 0
)


def stencil(PLEmb: FloatField, PLEmb_top: FloatFieldIJ, out_field: FloatField):
    with computation(FORWARD), interval(-1, None):
        PLEmb_top = PLEmb

    with computation(PARALLEL), interval(...):
        out_field = PLEmb_top


class Code:
    def __init__(
        self,
        stencil_factory: StencilFactory,
        qty_fctry: QuantityFactory,
    ):
        orchestrate(obj=self, config=stencil_factory.config.dace_config)
        self._tmp = qty_fctry.zeros([X_DIM, Y_DIM], "n/a")
        self.stencil = stcil_fctry.from_dims_halo(
            func=stencil,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )

    def __call__(self, PLEmb: FloatField, out_field: FloatField):
        self.stencil(PLEmb, self._tmp, out_field)


if __name__ == "__main__":
    I = np.ones(domain[0] * domain[1] * domain[2], dtype=np.float64).reshape(domain)
    I[:, :, domain[2] - 1] = 42
    O = np.zeros(domain)

    code = Code(stcil_fctry, ijk_qty_fctry)
    code(I, O)

    print(f"Input:\n{I}\n")
    print(f"Output:\n{O}\n")
    assert np.all(O == 42)
