import subprocess
from typing import Any, Optional, List
import os
import stat
from geosongpu_ci.utils.progress import Progress


class ShellScript:
    """Shell script utilities to write and execute"""

    def __init__(self, name, working_directory: str = ".") -> None:
        self._name = name
        self.working_directory = working_directory

    @property
    def path(self) -> str:
        return f"{self.working_directory}/{self._name}.sh"

    @property
    def name(self) -> str:
        return self._name

    def write(
        self,
        shell_commands: List[str],
        modules: Optional[List[str]] = None,
        env_to_source: Optional[List[str]] = None,
    ) -> "ShellScript":
        code = "#!/bin/sh\n"
        # Module load in prolog
        if modules:
            for m in modules:
                code += f"module load {m}\n"
            code += "\n"
        # Environment to source in prolog
        for env in env_to_source or []:
            if isinstance(env, ShellScript):
                code += f"source {env.path}\n"
            else:
                code += f"source {env}\n"
                code += "\n"

        # Script commands
        for c in shell_commands:
            code += f"{c}\n"
        code += "\n"

        # Write file
        with open(self.path, "w") as f:
            f.write(code)

        self._make_executable()
        return self

    def execute(self, remove_after_execution: bool = False) -> Any:
        # Execute
        result = self._execute_shell_script()
        if remove_after_execution:
            os.remove(self.path)
        return result

    def _make_executable(self):
        st = os.stat(self.path)
        os.chmod(self.path, st.st_mode | stat.S_IEXEC)

    def _execute_shell_script(self) -> str:
        with Progress(self.name):
            _make_executable(self.path)
            result = run_subprocess(
                self.path,
            )
        return result


def run_subprocess(command: str, print_log: bool = True) -> str:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
        )
        if print_log:
            print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(f"Subprocess with command {command}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Subprocess with command {command} failed, throwing error \n{e}"
        )
    return result.stdout


def _make_executable(name: str):
    st = os.stat(name)
    os.chmod(name, st.st_mode | stat.S_IEXEC)
