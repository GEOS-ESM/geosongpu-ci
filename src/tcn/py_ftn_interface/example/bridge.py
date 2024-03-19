# file plugin_build.py
import cffi

ffibuilder = cffi.FFI()

with open("data_to_be_transited.h") as f:
    data = "".join([line for line in f if not line.startswith("#")])
    data = data.replace("CFFI_DLLEXPORT", "")
    ffibuilder.embedding_api(data)

ffibuilder.set_source(
    "bridge",
    r"""#include "data_to_be_transited.h" """,
)

ffibuilder.embedding_init_code(
    """
    from bridge import ffi

    @ffi.def_extern()
    def python_function(data:"data_t"):
        print("In python_function")
        print(type(data))
        print(data.x, data.y)
"""
)

ffibuilder.compile(target="bridge.so", verbose=True)
