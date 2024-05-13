import numpy as np
from gt4py.cartesian.gtscript import (
    PARALLEL,
    computation,
    interval,
)
from ndsl import (
    StencilFactory,
    DaceConfig,
    orchestrate,
    QuantityFactory,
)
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl.dsl.typing import FloatField, Float

from ndsl_boilerplate import get_one_tile_factory_orchestrated

# ----- Model code ----- #


def localsum_stencil(
    field: FloatField,  # type: ignore
    result: FloatField,  # type: ignore
    weight: Float,  # type: ignore
):
    with computation(PARALLEL), interval(...):
        result = weight * (
            field[1, 0, 0] + field[0, 1, 0] + field[-1, 0, 0] + field[0, -1, 0]
        )


class LocalSum:
    def __init__(
        self, stencil_factory: StencilFactory, quantity_factory: QuantityFactory
    ) -> None:
        orchestrate(
            obj=self,
            config=stencil_factory.config.dace_config
            or DaceConfig(None, stencil_factory.backend),
        )
        grid_indexing = stencil_factory.grid_indexing
        self._local_sum = stencil_factory.from_origin_domain(
            localsum_stencil,  # <-- gt4py stencil function wrapped into NDSL
            origin=grid_indexing.origin_compute(),
            domain=grid_indexing.domain_compute(),
        )
        self._tmp_field = quantity_factory.zeros(
            [X_DIM, Y_DIM, Z_DIM], "n/a", dtype=dtype
        )
        self._n_halo = quantity_factory.sizer.n_halo

    def __call__(self, in_field: FloatField, out_result: FloatField) -> None:
        self._local_sum(in_field, out_result, 2.0)
        tmp_field = out_result[:, :, :] + 2
        self._local_sum(tmp_field, out_result, 2.0)


# ----- Driver ----- #

if __name__ == "__main__":
    # Settings
    backend = "dace:cpu"
    dtype = np.float64
    origin = (0, 0, 0)
    rebuild = True
    tile_size = (3, 3, 3)

    # Setup
    stencil_factory, qty_factory = get_one_tile_factory_orchestrated(
        nx=tile_size[0],
        ny=tile_size[1],
        nz=tile_size[2],
        nhalo=2,
        backend=backend,
    )
    local_sum = LocalSum(stencil_factory, qty_factory)

    in_field = qty_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a", dtype=dtype)
    in_field.view[:] = 2.0
    out_field = qty_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a", dtype=dtype)

    # Run
    local_sum(in_field, out_field)
