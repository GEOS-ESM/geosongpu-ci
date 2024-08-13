""" While loops in stencil functions

Last update: 2024/07/24
Description: gt4py allows while loop patterns in stencils. This pattern is also allowed to be 
    used in `gtscript.function`.
"""

from gt4py.cartesian.gtscript import computation, interval, PARALLEL, function
from ndsl.boilerplate import get_factories_single_tile_numpy
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl.dsl.typing import FloatField
from ndsl import StencilFactory, QuantityFactory, orchestrate
import numpy as np

domain = (3, 3, 4)

stcil_fctry, ijk_qty_fctry = get_factories_single_tile_numpy(
    domain[0], domain[1], domain[2], 0
)


@function
def while_in_function(field: FloatField):
    lev = 0
    while field[0, 0, lev] < 4:
        lev += 1
    return lev


def stencil(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL), interval(...):
        out_field = while_in_function(in_field)


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

    def __call__(self, I: FloatField, O: FloatField):
        self.stencil(I, O)


if __name__ == "__main__":
    I = np.ones(domain[0] * domain[1] * domain[2], dtype=np.float64).reshape(domain)
    I[:, :, domain[2] - 1] = 42
    O = np.zeros(domain)

    code = Code(stcil_fctry, ijk_qty_fctry)
    code(I, O)

    print(f"Input:\n{I}\n")
    print(f"Output:\n{O}\n")
    assert (O[0, 0, :] == [3.0, 2.0, 1.0, 0.0]).all()
