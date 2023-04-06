import subprocess
from typing import Optional, List
import os
import sys


def run_subprocess(command: str, stdout=None, stderr=None) -> str:
    # Run
    stdout = None
    try:
        stdout = subprocess.check_output(command).decode(sys.stdout.encoding)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Subprocess with command {command} failed, throwing error \n{e}"
        )
    return stdout


def execute_shell_script(name: str) -> str:
    return run_subprocess(name)


def shell_script(
    name: str,
    shell_commands: List[str],
    modules: Optional[List[str]] = None,
    env_to_source: Optional[str] = None,
    execute=True,
    temporary=False,
) -> Optional[str]:
    script = "#!/bin/sh\n"
    if modules:
        for m in modules:
            script += f"module load {m}\n"
        script += "\n"
    if env_to_source:
        script += f"source {env_to_source}\n"
        script += "\n"
    for c in shell_commands:
        script += f"{c}\n"
    script += "\n"

    with open(f"{name}.sh", "w") as f:
        f.write(script)

    if execute:
        result = execute_shell_script(name)
        if temporary:
            os.remove(name)
        return result
