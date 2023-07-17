from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.pipeline.geos import copy_input_from_project
from geosongpu_ci.utils.shell import shell_script, execute_shell_script
from typing import Dict, Any
import shutil
import os


def _replace_in_file(url: str, text_to_replace: str, new_text: str):
    with open(url, "r") as f:
        data = f.read()
        data = data.replace(text_to_replace, new_text)
    with open(url, "w") as f:
        f.write(data)


def _make_gpu_wrapper_script(geos_dir: str, layout: str):
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


def _set_python_environment(geos_install_dir: str, executable_name: str, geos_dir: str):
    geos_fvdycore_comp = (
        f"{geos_install_dir}/../src/Components/@GEOSgcm_GridComp/"
        "GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
    )
    shell_script(
        name="setenv",
        shell_commands=[
            f'echo "Copy execurable {executable_name}"',
            "",
            f"cp {geos_install_dir}/bin/{executable_name} {geos_dir}/experiment/l1x1",
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


def _make_srun_script(geos: str, executable_name: str, layout: str) -> str:
    srun_script_gpu_name = "srun_script_gpu.sh"
    exp_directory = f"{geos}/experiment/l{layout}"
    shell_script(
        name=srun_script_gpu_name.replace(".sh", ""),
        env_to_source=[
            "./setenv.sh",
        ],
        shell_commands=[
            f"cd {exp_directory}",
            "",
            "export FV3_DACEMODE=BuildAndRun",
            "export PACE_CONSTANTS=GEOS",
            "export PACE_FLOAT_PRECISION=32",
            "export PYTHONOPTIMIZE=1",
            "export PACE_LOGLEVEL=DEBUG",
            "export GTFV3_BACKEND=dace:gpu",
            f"export CUPY_CACHE_DIR={exp_directory}/.cupy",
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


@Registry.register
class HeldSuarez(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        geos_install_path = env.get("GEOS_INSTALL")
        geos = f"{geos_install_path}/.."
        layout = "1x1"

        copy_input_from_project(config, geos, layout)

        _make_gpu_wrapper_script(geos, layout)

        # TODO: cache build to not BuildAndRun all the time
        # TODO: mepo hash as a combination of all the hashes

        executable_name = "GEOShs.x"
        _set_python_environment(geos_install_path, executable_name, geos)

        srun_script_gpu_name = _make_srun_script(geos, executable_name, layout)

        # TODO: Fortran route equivalent to 1x6 on GPU

        if action == PipelineAction.Validation or action == PipelineAction.All:
            # Run the simulation as-is: one 3 timesteps
            execute_shell_script(srun_script_gpu_name)

        if action == PipelineAction.Benchmark or action == PipelineAction.All:
            # TODO: benchmark
            pass
            # Execute gtFV3
            _replace_in_file(
                srun_script_gpu_name,
                "--output=log.validation.%t.out",
                "--output=log.gtfv3.%t.out",
            )
            execute_shell_script(srun_script_gpu_name)

            # Execute Fortran
            # execute_shell_script(srun_script_fortran_name)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        geos_install_path = env.get("GEOS_INSTALL")
        geos_experiment_path = f"{geos_install_path}/../experiment"
        file_exists = os.path.isfile("ci_metadata")
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata. Coding or Permission error."
            )
        artifact_directory = f"{artifact_base_directory}/held_suarez/"
        os.mkdir(artifact_directory)
        shutil.copy("ci_metadata", artifact_directory)

        if action == PipelineAction.Validation or action == PipelineAction.All:
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.0.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.1.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.2.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.3.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.4.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/l1x1/log.validation.5.out", artifact_directory
            )

        return True
