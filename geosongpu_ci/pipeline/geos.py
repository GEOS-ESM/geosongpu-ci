from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.git import git_prelude
from geosongpu_ci.actions.discover import one_gpu_srun


def _epilogue(env: Environment):
    # Export GEOS_INSTALL for future scripts
    env.set(
        "GEOS_INSTALL",
        f"{env.CI_WORKSPACE}/geos/install",
    )


def _check(env: Environment) -> bool:
    return env.exists("GEOS_INSTALL")


GEOS_HS_KEY = "geos_hs"
GEOS_AQ_KEY = "geos_aq"


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
        if experiment_name == GEOS_AQ_KEY:
            cmake_cmd += " -DAQUAPLANET=ON"

        build_cmd = (
            f"{one_gpu_srun(log='build.out', time='00:30:00')} make -j12 install"
        )
        shell_script(
            name="build_geos",
            modules=[],
            env_to_source=[
                f"{env.CI_WORKSPACE}/geos/@env/g5_modules.sh",
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
        )

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


def copy_input_from_project(config: Dict[str, Any], geos_dir: str, layout: str):
    # Copy input
    input_config = config["input"]
    shell_script(
        name="copy_input",
        modules=[],
        shell_commands=[
            f"cd {geos_dir}",
            f"mkdir -p {geos_dir}/experiment/l{layout}",
            f"cd {geos_dir}/experiment/l{layout}",
            f"cp {input_config['directory']}/l{layout}/* .",
        ],
    )


def make_gpu_wrapper_script(geos_dir: str, layout: str):
    shell_script(
        name=f"{geos_dir}/experiment/l{layout}/gpu-wrapper-slurm",
        modules=[],
        shell_commands=[
            "#!/usr/bin/env sh",
            "export CUDA_VISIBLE_DEVICES=$SLURM_LOCALID",
            'echo "Node: $SLURM_NODEID | Rank: $SLURM_PROCID,'
            ' pinned to GPU: $CUDA_VISIBLE_DEVICES"',
            "$*",
        ],
        make_executable=True,
        execute=False,
    )


def set_python_environment(geos_install_dir: str, executable_name: str, geos_dir: str):
    geos_fvdycore_comp = (
        f"{geos_install_dir}/../src/Components/@GEOSgcm_GridComp/"
        "GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
    )
    shell_script(
        name="setenv",
        shell_commands=[
            f'echo "Copy execurable {executable_name}"',
            "",
            f"cp {geos_install_dir}/bin/{executable_name} {geos_dir}/experiment/1x6",
            "",
            'echo "Loading env (g5modules & pyenv)"',
            f"source {geos_install_dir}/../@env/g5_modules.sh",
            f'VENV_DIR="{geos_fvdycore_comp}/geos-gtfv3/driver/setenv/gtfv3_venv"',
            f'GTFV3_DIR="{geos_fvdycore_comp}/@gtFV3"',
            f'GEOS_INSTALL_DIR="{geos_install_dir}"',
            f"source {geos_fvdycore_comp}/geos-gtfv3/driver/setenv/pyenv.sh",
        ],
        execute=False,
    )


def make_srun_script(geos: str, executable_name: str, layout: str) -> str:
    srun_script_gpu_name = "srun_script_gpu.sh"
    shell_script(
        name=srun_script_gpu_name.replace(".sh", ""),
        env_to_source=[
            "./setenv.sh",
        ],
        shell_commands=[
            f"cd {geos}/experiment/l{layout}",
            "",
            "export FV3_DACEMODE=BuildAndRun",
            "export PACE_CONSTANTS=GEOS",
            "export PACE_FLOAT_PRECISION=32",
            "export PYTHONOPTIMIZE=1",
            "export PACE_LOGLEVEL=DEBUG",
            "export GTFV3_BACKEND=dace:gpu",
            "",
            "srun -A j1013 -C rome \\",
            "     --qos=4n_a100 --partition=gpu_a100 \\",
            "     --nodes=2 --ntasks=6 \\",
            "     --ntasks-per-node=3 --gpus-per-node=3 \\",
            "     --sockets-per-node=2 --mem-per-gpu=40G  \\",
            "     --time=1:00:00 \\",
            "     --output=log.validation.%t.out \\",
            f"     ./gpu-wrapper-slurm.sh ./{executable_name}",
        ],
        execute=False,
    )
    return srun_script_gpu_name
