# How to code
# do L=1,LM
#   do J=1,JM
#    do I=1,IM
#       ...
#       PLmb(i,j, KLCL(I,J))
#       ...
# See: https://github.com/GEOS-ESM/GEOSgcm_GridComp/blob/db55c301840d98b788b0e17045510af726c0f555/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/GEOS_GFDL_1M_InterfaceMod.F90#L589
# This code retuens O as a 2d field
# Line 31: ERROR when with computation(FORWARD) is changed to with computation(PARALLEL)
# This behavior has been flagged as a potential error with something under the hood

from gt4py.cartesian.gtscript import computation, interval, PARALLEL, FORWARD
from ndsl.boilerplate import get_factories_single_tile_numpy
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl.dsl.typing import FloatField, FloatFieldIJ, IntFieldIJ, IntField
from ndsl import StencilFactory, QuantityFactory, orchestrate
import numpy as np

domain = (3, 3, 4)
nhalo = 3
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
        #out_field: FloatField,
        k_mask: IntField,
        k_index_desired: IntFieldIJ,
        data_field: IntField,
    ):
        self.stencil(data_field, k_mask, k_index_desired, self.O)


if __name__ == "__main__":
    pressure = ijk_qty_fctry.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    k_index_desired = ijk_qty_fctry.zeros([X_DIM, Y_DIM], "n/a")
    k_mask = ijk_qty_fctry.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    for i in range(nhalo, domain[0]+nhalo):
        for j in range(nhalo, domain[1]+nhalo):
            k_index_desired.data[i, j] = np.random.randint(0, domain[2])
            for k in range(0,domain[2]):
                pressure.data[i, j, k] = np.random.randint(800,900)
                k_mask.data[i, j, k] = k

    code = Code(stcil_fctry, ijk_qty_fctry)
    code(k_mask, k_index_desired, pressure)

    print(f"Mask:\n{k_mask.data}\n")
    print(f"K Level Desired for each column:\n{k_index_desired.data}\n")
    print(f"Output:\n{code.O.data}\n")