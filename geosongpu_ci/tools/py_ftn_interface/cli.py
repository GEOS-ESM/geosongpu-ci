import click
import yaml
import os
from typing import List, Any, Dict
from itertools import chain
import subprocess
import clang_format as cf
import fprettify


class BridgeFunction:
    def __init__(
        self,
        name: str,
        inputs: List[Dict[str, str]],
        inouts: List[Dict[str, str]],
        outputs: List[Dict[str, str]],
    ) -> None:
        self.name = name
        self._inputs = inputs
        self._inouts = inouts
        self._outputs = outputs

    def _parse_c_argument_definitions(self, args, next_args) -> str:
        code = ""
        for argument in args:
            name, _type = list(argument.items())[0]
            if _type.startswith("array_"):
                _type = _type[len("array_") :] + "*"
            code += f"{_type} {name}, "
        if len(next_args) == 0:
            code = code[:-2]
        return code

    def generate_c(self, prefix: str) -> str:
        input_code_define = self._parse_c_argument_definitions(
            self._inputs, self._inouts
        )
        inout_code_define = self._parse_c_argument_definitions(
            self._inouts, self._outputs
        )
        output_code_define = self._parse_c_argument_definitions(self._outputs, [])

        prolog_code = ""
        for argument in chain(self._inputs, self._inouts, self._outputs):
            name, _type = list(argument.items())[0]
            if _type.startswith("array_"):
                _type = _type[len("array_") :] + "*"
            if _type == "MPI":
                prolog_code += f"MPI_Comm {name}_c = MPI_Comm_f2c({name});"

        argument_call_code = ""
        for argument in chain(self._inputs, self._inouts, self._outputs):
            name, _type = list(argument.items())[0]
            if _type.startswith("array_"):
                _type = _type[len("array_") :] + "*"
            argument_call_code += f"{name}, "
        argument_call_code = argument_call_code[:-2]

        c_bridge_code = """void {PREFIX}_{FUNCTION_NAME}_c(
                //inputs
                {ARGUMENTS_DEF_INPUT}
                //inputs-outputs
                {ARGUMENTS_DEF_INOUT}
                //outputs
                {ARGUMENTS_DEF_OUTPUT}
                )
            {{
                {PROLOG}
                {PREFIX}_interface_py_{FUNCTION_NAME}({ARGUMENTS_CALL});
            }}
            """.format(
            PREFIX=prefix,
            FUNCTION_NAME=self.name,
            ARGUMENTS_DEF_INPUT=input_code_define,
            ARGUMENTS_DEF_INOUT=inout_code_define,
            ARGUMENTS_DEF_OUTPUT=output_code_define,
            PROLOG=prolog_code,
            ARGUMENTS_CALL=argument_call_code,
        )

        return c_bridge_code

    def _parse_ftn_argument_definitions(self, args) -> str:
        code = ""
        for i, argument in enumerate(args):
            name, _type = list(argument.items())[0]
            code += f"{name}, "
            if (i + 1) % 10 == 0:
                code += "&\n"
        if code != "":
            code += "&"
        return code

    def _fortran_type_declaration(self, def_type: str, intent: str, name: str) -> str:
        if def_type == "int":
            return f"integer(kind=c_int), value, intent({intent}) :: {name} \n"
        elif def_type == "float":
            return f"real(kind=c_float), value, intent({intent}) :: {name} \n"
        elif def_type == "double":
            return f"real(kind=c_double), value, intent({intent}) :: {name} \n"
        elif def_type == "array_int":
            return f"integer(kind=c_int), dimension(*), intent({intent}) :: {name} \n"
        elif def_type == "array_float":
            return f"integer(kind=c_float), dimension(*), intent({intent}) :: {name} \n"
        elif def_type == "array_double":
            return (
                f"integer(kind=c_double), dimension(*), intent({intent}) :: {name} \n"
            )
        elif def_type == "MPI":
            return f"integer(kind=c_int), value, intent(in) :: {name} \n"
        else:
            return "ERROR_DEF_TYPE_TO_FORTRAN"

    def generate_ftn(self, prefix: str) -> str:
        input_code_define = self._parse_ftn_argument_definitions(self._inputs)
        inout_code_define = self._parse_ftn_argument_definitions(self._inouts)
        output_code_define = self._parse_ftn_argument_definitions(self._outputs)

        declaration_code = ""
        for argument in self._inputs:
            name, _type = list(argument.items())[0]
            declaration_code += self._fortran_type_declaration(_type, "in", name)
        for argument in self._inouts:
            name, _type = list(argument.items())[0]
            declaration_code += self._fortran_type_declaration(_type, "inout", name)
        for argument in self._outputs:
            name, _type = list(argument.items())[0]
            declaration_code += self._fortran_type_declaration(_type, "out", name)

        ftn_bridge_code = """subroutine {PREFIX}_{FUNCTION_NAME}_f( &
                !inputs
                {ARGUMENTS_DEF_INPUT}
                !inputs-outputs
                {ARGUMENTS_DEF_INOUT}
                !outputs
                {ARGUMENTS_DEF_OUTPUT}
                ) bind(c, name='{PREFIX}_{FUNCTION_NAME}_c')

                import c_int, c_float, c_double
                implicit none

                {ARGUMENTS_DECLARATION}

            end subroutine  {PREFIX}_{FUNCTION_NAME}_f
            """.format(
            PREFIX=prefix,
            FUNCTION_NAME=self.name,
            ARGUMENTS_DEF_INPUT=input_code_define,
            ARGUMENTS_DEF_INOUT=inout_code_define,
            ARGUMENTS_DEF_OUTPUT=output_code_define,
            ARGUMENTS_DECLARATION=declaration_code,
        )

        return ftn_bridge_code

    def _parse_py_argument_definitions(self, args, next_args) -> str:
        code = ""
        for argument in args:
            name, _type = list(argument.items())[0]
            if _type.startswith("array_"):
                _type = "'cffi.FFI.CData'"
            if _type == "MPI":
                _type = "MPI.Intercomm"
            code += f"{name}: {_type}, "
        if len(next_args) == 0:
            code = code[:-2]
        return code

    def generate_py(self, prefix: str) -> str:
        input_code_define = self._parse_py_argument_definitions(
            self._inputs, self._inouts
        )
        inout_code_define = self._parse_py_argument_definitions(
            self._inouts, self._outputs
        )
        output_code_define = self._parse_py_argument_definitions(self._outputs, [])

        prolog_code = ""
        for argument in chain(self._inputs, self._inouts, self._outputs):
            name, _type = list(argument.items())[0]
            if _type == "MPI":
                prolog_code += """
    # {NAME} -> comm_py
    comm_py = MPI.Intracomm() # new comm, internal MPI_Comm handle is MPI_COMM_NULL
    comm_ptr = MPI._addressof(comm_py)  # internal MPI_Comm handle
    comm_ptr = ffi.cast('{{}}*', comm_ptr)  # make it a CFFI pointer
    comm_ptr[0] = {NAME}  # assign comm_c to comm_py's MPI_Comm handle
                """.format(
                    NAME=name
                )

        comm_count = 0
        argument_call_code = ""
        for argument in chain(self._inputs, self._inouts, self._outputs):
            name, _type = list(argument.items())[0]
            if _type == "MPI":
                name = "comm_py"
                comm_count += 1
            argument_call_code += f"{name}, "
        argument_call_code = argument_call_code[:-2]

        py_bridge_code = """
@ffi.def_extern()
def {PREFIX}_{FUNCTION_NAME}_py(
    #inputs
    {ARGUMENTS_DEF_INPUT}
    #inputs-outputs
    {ARGUMENTS_DEF_INOUT}
    #outputs
    {ARGUMENTS_DEF_OUTPUT}
    ):
    {PROLOG}
    {PREFIX}_{FUNCTION_NAME}({ARGUMENTS_CALL})

            """.format(
            PREFIX=prefix,
            FUNCTION_NAME=self.name,
            ARGUMENTS_DEF_INPUT=input_code_define,
            ARGUMENTS_DEF_INOUT=inout_code_define,
            ARGUMENTS_DEF_OUTPUT=output_code_define,
            PROLOG=prolog_code,
            ARGUMENTS_CALL=argument_call_code,
        )

        return py_bridge_code

    def generate_hook(self, prefix: str) -> str:
        input_code_define = self._parse_py_argument_definitions(
            self._inputs, self._inouts
        )
        inout_code_define = self._parse_py_argument_definitions(
            self._inouts, self._outputs
        )
        output_code_define = self._parse_py_argument_definitions(self._outputs, [])

        py_hook_code = """
def {PREFIX}_{FUNCTION_NAME}(
    #inputs
    {ARGUMENTS_DEF_INPUT}
    #inputs-outputs
    {ARGUMENTS_DEF_INOUT}
    #outputs
    {ARGUMENTS_DEF_OUTPUT}
    ):
        print("My code for {PREFIX}_{FUNCTION_NAME} geos here.")
        """.format(
            PREFIX=prefix,
            FUNCTION_NAME=self.name,
            ARGUMENTS_DEF_INPUT=input_code_define,
            ARGUMENTS_DEF_INOUT=inout_code_define,
            ARGUMENTS_DEF_OUTPUT=output_code_define,
        )

        return py_hook_code


class Bridge:
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[BridgeFunction],
    ) -> None:
        self._directory_path = directory_path
        self._prefix = prefix
        self._functions = function_defines

    def generate_c(self) -> "Bridge":
        header = """
            #include <stdio.h>
            #include <time.h>
            #include "mpi.h"
            #include "{PREFIX}_interface_py.h"
            """.format(
            PREFIX=self._prefix
        )
        code = ""
        for function in self._functions:
            code += function.generate_c(self._prefix)

        c_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.c"
        with open(c_source_filepath, "w+") as f:
            f.write(header + code)

        # Format
        subprocess.call([cf._get_executable("clang-format"), "-i", c_source_filepath])

        return self

    def generate_fortran(self) -> "Bridge":
        header = """
            module {PREFIX}_interface_mod

            use iso_c_binding, only: c_int, c_float, c_double

            implicit none

            private
            """.format(
            PREFIX=self._prefix
        )
        for function in self._functions:
            header += "public :: {PREFIX}_{FUNCTION_NAME}_f\n".format(
                PREFIX=self._prefix, FUNCTION_NAME=function.name
            )

        header += "interface\n"

        code = ""
        for function in self._functions:
            code += function.generate_ftn(self._prefix)

        footer = """

            end interface
            end module {PREFIX}_interface_mod
        """.format(
            PREFIX=self._prefix
        )

        ftn_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.f90"
        with open(ftn_source_filepath, "w+") as f:
            f.write(header + code + footer)

        # Format
        fprettify.reformat_inplace(ftn_source_filepath)

        return self

    def generate_python(self) -> "Bridge":
        header = """
import cffi
from mpi4py import MPI

TMPFILEBASE = "{PREFIX}_interface_py"

ffi = cffi.FFI()

# MPI_Comm can be int or void*
if MPI._sizeof(MPI.Comm) == ffi.sizeof("int"):
    _mpi_comm_t = "int"
else:
    _mpi_comm_t = "void*"
    
            """.format(
            PREFIX=self._prefix
        )

        # Source
        source = """
source=\"""
from {} import ffi
from datetime import datetime
from mpi4py import MPI

        """
        source += """
from {PREFIX} import """.format(
            PREFIX=self._prefix
        )
        for function in self._functions:
            source += "{PREFIX}_{FUNCTION_NAME}, ".format(
                PREFIX=self._prefix, FUNCTION_NAME=function.name
            )
        source = source[:-2] + "\n\n"

        for function in self._functions:
            source += function.generate_py(self._prefix)

        source += '""".format(TMPFILEBASE,'
        for function in self._functions:
            for argument in chain(
                function._inputs, function._inouts, function._outputs
            ):
                _name, _type = list(argument.items())[0]
                if _type == "MPI":
                    source += "_mpi_comm_t, "
        source = source[:-2] + ")\n"

        # C Header gen
        c_header = 'header="""\n'
        for function in self._functions:
            c_header += """
extern void {PREFIX}_{FUNCTIONNAME}(""".format(
                PREFIX=self._prefix, FUNCTIONNAME=function.name
            )

            no_args = True
            for argument in chain(
                function._inputs, function._inouts, function._outputs
            ):
                no_args = False
                name, _type = list(argument.items())[0]
                if _type == "MPI":
                    c_header += "{} " + name + ", "
                else:
                    c_header += f"{name}, "
            if not no_args:
                c_header = c_header[:-2]
            c_header += ");"
        c_header += '""".format('
        for function in self._functions:
            for argument in chain(
                function._inputs, function._inouts, function._outputs
            ):
                _name, _type = list(argument.items())[0]
                if _type == "MPI":
                    c_header += "_mpi_comm_t, "
        c_header = c_header[:-2] + ")\n"

        # Footer
        footer = """
with open(TMPFILEBASE + ".h", "w") as f:
    f.write(header)
    ffi.embedding_api(header)

    source_header = r'''#include "{}.h"'''.format(TMPFILEBASE)
    ffi.set_source(TMPFILEBASE, source_header)

    ffi.embedding_init_code(source)
    ffi.compile(target="lib" + TMPFILEBASE + ".so", verbose=True)

        """

        py_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.py"
        with open(py_source_filepath, "w+") as f:
            f.write(header + source + c_header + footer)

        # Format
        subprocess.call(["black", "-q", py_source_filepath])

        return self


class Hook:
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[BridgeFunction],
    ) -> None:
        self._directory_path = directory_path
        self._prefix = prefix
        self._functions = function_defines

    def generate_blank(self):
        header = """
from f_py_conversion import FortranPythonConversion
from cuda_profiler import CUDAProfiler, TimedCUDAProfiler
from mpi4py import MPI
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cffi

        """

        source = ""
        for function in self._functions:
            source += function.generate_hook(self._prefix)

        py_source_filepath = f"./{self._directory_path}/{self._prefix}_hook.py"
        with open(py_source_filepath, "w+") as f:
            f.write(header + source)

        # Format
        subprocess.call(["black", "-q", py_source_filepath])

        return self

    def generate_obj(self):
        pass


class Build:
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[BridgeFunction],
    ) -> None:
        self._directory_path = directory_path
        self._prefix = prefix
        self._functions = function_defines

    def generate_cmake(self):
        pass


@click.command()
@click.argument("definition_json_filepath")
@click.option(
    "--directory",
    default="gt_interface",
    help="Directory name to drop interface files in",
)
@click.option("--hook", default="blank")
@click.option("--build", default="cmake")
def cli(definition_json_filepath: str, directory: str, hook: str, build: str):
    with open(definition_json_filepath) as f:
        defs = yaml.safe_load(f)
    if "type" not in defs.keys() and defs["type"] == "py_ftn_interface":
        raise RuntimeError("Bad definition")

    # Make directory
    os.makedirs(directory, exist_ok=True)

    # Make bridge
    prefix = defs["name"]
    functions = []
    for function_name, args in defs["functions"].items():
        if args == "None":
            args = None
        functions.append(
            BridgeFunction(
                function_name,
                (args["inputs"] if "inputs" in args.keys() else []) if args else [],
                (args["inouts"] if "inouts" in args.keys() else []) if args else [],
                (args["outputs"] if "outputs" in args.keys() else []) if args else [],
            )
        )

    Bridge(
        directory,
        prefix,
        functions,
    ).generate_c().generate_fortran().generate_python()

    h = Hook(directory, prefix, functions)
    if hook == "blank":
        h.generate_blank()
    else:
        raise NotImplementedError(f"No hook '{hook}'")

    b = Build(directory, prefix, functions)
    if build == "cmake":
        b.generate_cmake()
    else:
        raise NotImplementedError(f"No build '{build}'")

    # Make converter (CPU/GPU & Py/Fortran)


if __name__ == "__main__":
    cli()
