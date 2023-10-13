import click
import yaml
import os
from typing import List, Dict
import subprocess
import clang_format as cf
import fprettify
import jinja2
import textwrap


class BridgeFunction:
    def __init__(
        self,
        name: str,
        inputs: Dict[str, str],
        inouts: Dict[str, str],
        outputs: Dict[str, str],
    ) -> None:
        self.name = name
        self._inputs = inputs
        self._inouts = inouts
        self._outputs = outputs

    @property
    def inputs(self) -> Dict[str, str]:
        return self._inputs

    @property
    def outputs(self) -> Dict[str, str]:
        return self._outputs

    @property
    def inouts(self) -> Dict[str, str]:
        return self._inouts

    @property
    def arguments(self) -> Dict[str, str]:
        return {**self._inputs, **self._inouts, **self._outputs}

    @staticmethod
    def c_arguments_for_jinja2(arguments: Dict[str, str]) -> List[Dict[str, str]]:
        """Transform yaml input for the template renderer"""
        trf_args = []
        for name, _type in arguments.items():
            if _type.startswith("array_"):
                _type = _type[len("array_") :] + "*"
            trf_args.append({"type": _type, "name": name})

        return trf_args

    @staticmethod
    def fortran_arguments_for_jinja2(arguments: Dict[str, str]) -> List[Dict[str, str]]:
        """Transform yaml input for the template renderer"""
        trf_args = []
        for name, _type in arguments.items():
            _type = BridgeFunction._fortran_type_declaration(_type)
            trf_args.append({"type": _type, "name": name})

        return trf_args

    @staticmethod
    def py_arguments_for_jinja2(arguments: Dict[str, str]) -> List[Dict[str, str]]:
        """Transform yaml input for the template renderer"""
        trf_args = []
        for name, _type in arguments.items():
            if _type.startswith("array_"):
                _type = "'cffi.FFI.CData'"
            if _type == "MPI":
                _type = "MPI.Intercomm"
            trf_args.append({"type": _type, "name": name})
        return trf_args

    def py_init_code(self) -> List[str]:
        code = []
        for name, _type in self.arguments.items():
            if _type == "MPI":
                _type = "MPI.Intercomm"
                code.append(
                    textwrap.dedent(
                        f"""\
                        # Comm translate to python
                            comm_py = MPI.Intracomm() # new comm, internal MPI_Comm handle is MPI_COMM_NULL
                            comm_ptr = MPI._addressof(comm_py)  # internal MPI_Comm handle
                            comm_ptr = ffi.cast('{{_mpi_comm_t}}*', comm_ptr)  # make it a CFFI pointer
                            comm_ptr[0] = {name}  # assign comm_c to comm_py's MPI_Comm handle
                            {name} = comm_py # Override the symbol name to make life easier for code gen"""
                    )
                )
        return code

    def c_init_code(self) -> List[str]:
        prolog_code = []
        for name, _type in self.arguments.items():
            if _type == "MPI":
                prolog_code.append(f"MPI_Comm {name}_c = MPI_Comm_f2c({name});")
        return prolog_code

    def arguments_name(self) -> List[str]:
        call = []
        for name, _type in self.arguments.items():
            call.append(name)
        return call

    @staticmethod
    def _fortran_type_declaration(def_type: str) -> str:
        if def_type == "int":
            return "integer(kind=c_int), value"
        elif def_type == "float":
            return "real(kind=c_float), value"
        elif def_type == "double":
            return "real(kind=c_double), value"
        elif def_type == "array_int":
            return "integer(kind=c_int), dimension(*)"
        elif def_type == "array_float":
            return "integer(kind=c_float), dimension(*)"
        elif def_type == "array_double":
            return "integer(kind=c_double), dimension(*)"
        elif def_type == "MPI":
            return "integer(kind=c_int), value"
        else:
            raise RuntimeError(f"ERROR_DEF_TYPE_TO_FORTRAN: {def_type}")

    def _parse_py_argument_definitions(self, args, next_args) -> str:
        code = ""
        for name, _type in args.items():
            if _type.startswith("array_"):
                _type = "'cffi.FFI.CData'"
            if _type == "MPI":
                _type = "MPI.Intercomm"
            code += f"{name}: {_type}, "
        if len(next_args) == 0:
            code = code[:-2]
        return code

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
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": BridgeFunction.c_arguments_for_jinja2(function.inputs),
                    "inouts": BridgeFunction.c_arguments_for_jinja2(function.inouts),
                    "ouputs": BridgeFunction.c_arguments_for_jinja2(function.outputs),
                    "arguments_init": function.c_init_code(),
                    "arguments_name": function.arguments_name(),
                }
            )

        # TODO: replace hard coded by deployed template directory or local for dev
        template_loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(
                "/home/fgdeconi/work/git/geosongpu-ci/geosongpu_ci/tools/py_ftn_interface",
                "templates",
            )
        )
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("interface.c.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
        )

        c_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.c"
        with open(c_source_filepath, "w+") as f:
            f.write(code)

        # Format
        subprocess.call([cf._get_executable("clang-format"), "-i", c_source_filepath])

        return self

    def generate_fortran(self) -> "Bridge":
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": BridgeFunction.fortran_arguments_for_jinja2(
                        function.inputs
                    ),
                    "inouts": BridgeFunction.fortran_arguments_for_jinja2(
                        function.inouts
                    ),
                    "ouputs": BridgeFunction.fortran_arguments_for_jinja2(
                        function.outputs
                    ),
                }
            )

        # TODO: replace hard coded by deployed template directory or local for dev
        template_loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(
                "/home/fgdeconi/work/git/geosongpu-ci/geosongpu_ci/tools/py_ftn_interface",
                "templates",
            )
        )
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("interface.f90.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
        )

        ftn_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.f90"
        with open(ftn_source_filepath, "w+") as f:
            f.write(code)

        # Format
        fprettify.reformat_inplace(ftn_source_filepath)

        return self

    def generate_python(self) -> "Bridge":
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": BridgeFunction.py_arguments_for_jinja2(function.inputs),
                    "inouts": BridgeFunction.py_arguments_for_jinja2(function.inouts),
                    "ouputs": BridgeFunction.py_arguments_for_jinja2(function.outputs),
                    "init_code": function.py_init_code(),
                    "all_arguments_name": function.arguments_name(),
                    "c_arguments": BridgeFunction.c_arguments_for_jinja2(
                        function.arguments
                    ),
                }
            )

        # TODO: replace hard coded by deployed template directory or local for dev
        template_loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(
                "/home/fgdeconi/work/git/geosongpu-ci/geosongpu_ci/tools/py_ftn_interface",
                "templates",
            )
        )
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("interface.py.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
        )

        py_source_filepath = f"./{self._directory_path}/{self._prefix}_interface.py"
        with open(py_source_filepath, "w+") as f:
            f.write(code)

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
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": BridgeFunction.py_arguments_for_jinja2(function.inputs),
                    "inouts": BridgeFunction.py_arguments_for_jinja2(function.inouts),
                    "ouputs": BridgeFunction.py_arguments_for_jinja2(function.outputs),
                }
            )

        # TODO: replace hard coded by deployed template directory or local for dev
        template_loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(
                "/home/fgdeconi/work/git/geosongpu-ci/geosongpu_ci/tools/py_ftn_interface",
                "templates",
            )
        )
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("hook.py.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
        )

        py_source_filepath = f"./{self._directory_path}/{self._prefix}_hook.py"
        with open(py_source_filepath, "w+") as f:
            f.write(code)

        # Format
        subprocess.call(["black", "-q", py_source_filepath])

        return self

    def generate_obj(self):
        raise NotImplementedError("Not implemented")


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
                (args["inputs"] if "inputs" in args.keys() else {}) if args else {},
                (args["inouts"] if "inouts" in args.keys() else {}) if args else {},
                (args["outputs"] if "outputs" in args.keys() else {}) if args else {},
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
