from typing import Any, Dict, Optional

from tcn.ci.actions.discover import one_gpu_srun
from tcn.ci.actions.git import git_prelude
from tcn.ci.pipeline.task import TaskBase
from tcn.utils.environment import Environment
from tcn.utils.progress import Progress
from tcn.utils.registry import Registry
from tcn.utils.shell import ShellScript


def _epilogue(env: Environment):
    # Export GEOS_INSTALL for future scripts
    env.set(
        "GEOS_INSTALL_DIRECTORY",
        f"{env.CI_WORKSPACE}/geos/install",
    )
    env.set(
        "GEOS_BASE_DIRECTORY",
        f"{env.CI_WORKSPACE}/geos/",
    )


def _check(env: Environment) -> bool:
    return env.exists("GEOS_INSTALL_DIRECTORY") and env.exists("GEOS_BASE_DIRECTORY")


GEOS_HS_KEY = "geos_hs"
GEOS_AQ_KEY = "geos_aq"


def set_python_environment(
    geos_directory: str,
    geos_install_dir: str,
    working_directory: str = ".",
) -> ShellScript:
    """Set a python environment using FVDycore GridComp auto-env script"""
    geos_fvdycore_comp = (
        f"{geos_directory}/src/Components/@GEOSgcm_GridComp/"
        "GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
    )

    set_env = ShellScript("setenv", working_directory)
    set_env.write(
        shell_commands=[
            'echo "Loading env (g5modules & pyenv)"',
            f"source {geos_directory}/@env/g5_modules.sh",
            f'VENV_DIR="{geos_fvdycore_comp}/geos-gtfv3/driver/setenv/gtfv3_venv"',
            f'GTFV3_DIR="{geos_fvdycore_comp}/@gtFV3"',
            f'GEOS_INSTALL_DIR="{geos_install_dir}"',
            f"source {geos_fvdycore_comp}/geos-gtfv3/driver/setenv/pyenv.sh",
        ],
    )
    return set_env


def copy_input_to_experiment_directory(
    input_directory: str,
    geos_directory: str,
    resolution: str,
    experiment_name: Optional[str] = None,
    trigger_reset: bool = False,
) -> str:
    """Copy the input directory into the experiment directory.

    Optionally, trigger the "reset.sh" to get data clean and ready to execute.
    """
    if experiment_name:
        experiment_dir = f"{geos_directory}/experiment/{experiment_name}"
    else:
        experiment_dir = f"{geos_directory}/experiment/{resolution}"

    if trigger_reset:
        reset_cmd = "./reset.sh"
    else:
        reset_cmd = ""

    ShellScript(f"copy_input_{resolution}").write(
        modules=[],
        shell_commands=[
            f"cd {geos_directory}",
            f"mkdir -p {experiment_dir}",
            f"cd {experiment_dir}",
            f"cp -r {input_directory}/* .",
            reset_cmd,
        ],
    ).execute()
    return experiment_dir


@Registry.register
class GEOS(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        git_prelude(
            config,
            env.experiment_name,
            env.experiment_action,
            metadata,
            override_repo_name="geos",
            do_mepo=True,
        )

        set_env_script = set_python_environment(
            geos_directory=f"{env.CI_WORKSPACE}/geos",
            geos_install_dir=f"{env.CI_WORKSPACE}/geos/install",
        )

        # Build GEOS with GTFV3 interface
        cmake_cmd = "cmake .."
        cmake_cmd += " -DBASEDIR=$BASEDIR/Linux"
        cmake_cmd += " -DCMAKE_Fortran_COMPILER=gfortran"
        cmake_cmd += " -DBUILD_GEOS_GTFV3_INTERFACE=ON"
        cmake_cmd += " -DCMAKE_INSTALL_PREFIX=../install"
        cmake_cmd += " -DPython3_EXECUTABLE=`which python3`"
        if env.experiment_name == GEOS_AQ_KEY:
            cmake_cmd += " -DAQUAPLANET=ON"

        ShellScript("geos_build_CMake").write(
            modules=[],
            env_to_source=[
                set_env_script,
            ],
            shell_commands=[
                "cd geos",
                "mkdir build",
                "cd build",
                f"export TMP={env.CI_WORKSPACE}/geos/build/tmp",
                "export TMPDIR=$TMP",
                "export TEMP=$TMP",
                "mkdir $TMP",
                "echo $TMP",
                cmake_cmd,
            ],
        ).execute()

        build_cmd = (
            f"{one_gpu_srun(log='build.out', time='01:30:00')} make -j48 install"
        )
        make_script = ShellScript("geos_build_make")
        make_script.write(
            modules=[],
            env_to_source=[
                set_env_script,
            ],
            shell_commands=[
                "cd geos/build",
                f"export TMP={env.CI_WORKSPACE}/geos/build/tmp",
                build_cmd,
            ],
        )
        if not env.setup_only:
            make_script.execute()
        else:
            Progress.log(f"= = = Skipping {make_script.name} = = =")

        _epilogue(env)

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        return _check(env)
