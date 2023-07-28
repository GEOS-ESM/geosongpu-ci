from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import ShellScript
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.git import git_prelude
from geosongpu_ci.actions.discover import one_gpu_srun


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


@Registry.register
class GEOS(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        git_prelude(
            config,
            experiment_name,
            action,
            metadata,
            override_repo_name="geos",
            do_mepo=True,
        )

        # Build GEOS with GTFV3 interface
        cmake_cmd = "cmake .."
        cmake_cmd += " -DBASEDIR=$BASEDIR/Linux"
        cmake_cmd += " -DCMAKE_Fortran_COMPILER=gfortran"
        cmake_cmd += " -DBUILD_GEOS_GTFV3_INTERFACE=ON"
        cmake_cmd += " -DCMAKE_INSTALL_PREFIX=../install"
        cmake_cmd += " -DPython3_EXECUTABLE=`which python3`"
        if experiment_name == GEOS_AQ_KEY:
            cmake_cmd += " -DAQUAPLANET=ON"

        set_env_script = set_python_environment(
            geos_directory=f"{env.CI_WORKSPACE}/geos",
            geos_install_dir=f"{env.CI_WORKSPACE}/geos/install",
        )

        build_cmd = (
            f"{one_gpu_srun(log='build.out', time='01:30:00')} make -j48 install"
        )
        script = ShellScript("build_geos")
        script.write(
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
                build_cmd,
            ],
            execute=False,
        )
        if not env.setup_only:
            script.execute(script)
        else:
            print(f"= = = Skipping {script}")

        _epilogue(env)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(env)


def copy_input_from_project(config: Dict[str, Any], geos_dir: str, layout: str) -> str:
    # Copy input
    input_config = config["input"]
    experiment_dir = f"{geos_dir}/experiment/l{layout}"
    ShellScript("copy_input").write(
        shell_commands=[
            f"cd {geos_dir}",
            f"mkdir -p {geos_dir}/experiment/l{layout}",
            f"cd {experiment_dir}",
            f"cp -r {input_config['directory']}/l{layout}/* .",
        ],
    ).execute()
    return experiment_dir
