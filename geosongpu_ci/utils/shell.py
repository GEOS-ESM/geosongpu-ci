import subprocess
from typing import Optional, List, Union
import os
import sys
import stat


# ToDo: refactor shell_script into this
class Script:
    def __init__(self, name, working_directory: str = ".") -> None:
        self._name = name
        self.working_directory = working_directory

    @property
    def sh(self) -> str:
        return f"{self.working_directory}/{self._name}.sh"

    @property
    def name(self) -> str:
        return self._name


def run_subprocess(command: str, stdout=None, stderr=None) -> str:
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"Subprocess with command {command}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Subprocess with command {command} failed, throwing error \n{e}"
        )
    return result.stdout.decode(sys.stdout.encoding)


def _make_executable(name: str):
    st = os.stat(name)
    os.chmod(name, st.st_mode | stat.S_IEXEC)


def execute_shell_script(script: Union[str, Script]) -> str:
    name = script.sh if isinstance(script, Script) else script
    print(f"> > > Executing {name}")
    _make_executable(name)
    return run_subprocess(name, stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)


def shell_script(
    name: str,
    shell_commands: List[str],
    working_directory: str = ".",
    modules: Optional[List[str]] = None,
    env_to_source: Optional[List[str]] = None,
    make_executable=True,
    execute=True,
    temporary=False,
) -> Optional[str]:
    script = "#!/bin/sh\n"
    if modules:
        for m in modules:
            script += f"module load {m}\n"
        script += "\n"
    for env in env_to_source or []:
        if isinstance(env, Script):
            script += f"source {env.sh}\n"
        else:
            script += f"source {env}\n"
            script += "\n"
    for c in shell_commands:
        script += f"{c}\n"
    script += "\n"

    script_name = f"{working_directory}/{name}.sh"
    with open(script_name, "w") as f:
        f.write(script)

    if make_executable:
        _make_executable(script_name)

    if execute:
        result = execute_shell_script(script_name)
        if temporary:
            os.remove(script_name)
        return result
