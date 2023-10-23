from typing import Optional
import yaml


class Argument:
    def __init__(self, name: str, type: str, dims: Optional[int] = None) -> None:
        self._name = name
        self._type = type
        self._dims = dims

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_sanitize(self) -> str:
        if self._name in ["is", "in"]:
            return f"_{self._name}"
        return self.name

    @property
    def yaml_type(self) -> str:
        return self._type

    @property
    def c_type(self) -> str:
        if self._type.startswith("array_"):
            return self._type[len("array_") :] + "*"
        if self._type.startswith("MPI"):
            return "void*"
        return self._type

    @property
    def py_type_hint(self) -> str:
        if self._type.startswith("array_"):
            return "'cffi.FFI.CData'"
        if self._type == "MPI":
            return "MPI.Intercomm"
        return self._type

    @property
    def f90_type_definition(self) -> str:
        if self._type == "int":
            return "integer(kind=c_int), value"
        elif self._type == "float":
            return "real(kind=c_float), value"
        elif self._type == "double":
            return "real(kind=c_double), value"
        elif self._type == "array_int":
            return "integer(kind=c_int), dimension(*)"
        elif self._type == "array_float":
            return "real(kind=c_float), dimension(*)"
        elif self._type == "array_double":
            return "real(kind=c_double), dimension(*)"
        elif self._type == "MPI":
            return "integer(kind=c_int), value"
        else:
            raise RuntimeError(f"ERROR_DEF_TYPE_TO_FORTRAN: {self._type}")


def argument_constructor(
    loader: yaml.SafeLoader, node: yaml.nodes.MappingNode
) -> Argument:
    return Argument(**loader.construct_mapping(node))  # noqa


def get_argument_yaml_loader():
    loader = yaml.SafeLoader
    loader.add_constructor("!Argument", argument_constructor)
    return loader
