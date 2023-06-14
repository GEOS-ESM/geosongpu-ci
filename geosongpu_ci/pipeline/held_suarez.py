from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
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

        # Copy input
        input_config = config["input"]
        shell_script(
            name="copy_input",
            modules=[],
            shell_commands=[
                f"cd {geos}",
                f"mkdir -p {geos}/experiment/1x6",
                f"cd {geos}/experiment/1x6",
                f"cp {input_config['directory']}/1x6/* .",
                f"mkdir -p {geos}/experiment/3x24",
                f"cd {geos}/experiment/3x24",
                f"cp {input_config['directory']}/3x24/* .",
            ],
        )

        shell_script(
            name=f"{geos}/experiment/1x6/gpu-wrapper-slurm",
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
        shell_script(
            name=f"{geos}/experiment/3x24/gpu-wrapper-slurm",
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

        # TODO: cache build to not BuildAndRun all the time
        # TODO: mepo hash as a combination of all the hashes

        executable_name = "GEOShs.x"

        # Run
        geos_fvdycore_comp = (
            f"{geos_install_path}/../src/Components/@GEOSgcm_GridComp/"
            "GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
        )
        shell_script(
            name="setenv",
            shell_commands=[
                f'echo "Copy execurable {executable_name}"',
                "",
                f"cp {geos_install_path}/bin/{executable_name} {geos}/experiment/1x6",
                f"cp {geos_install_path}/bin/{executable_name} {geos}/experiment/3x24",
                "",
                'echo "Loading env (g5modules & pyenv)"',
                f"source {geos_install_path}/../@env/g5_modules.sh",
                f'VENV_DIR="{geos_fvdycore_comp}/geos-gtfv3/driver/setenv/gtfv3_venv"',
                f'GTFV3_DIR="{geos_fvdycore_comp}/@gtFV3"',
                f'GEOS_INSTALL_DIR="{geos_install_path}"',
                f"source {geos_fvdycore_comp}/geos-gtfv3/driver/setenv/pyenv.sh",
            ],
            execute=False,
        )

        srun_script_gpu_name = "srun_script_gpu.sh"
        shell_script(
            name=srun_script_gpu_name.replace(".sh", ""),
            env_to_source=[
                "./setenv.sh",
            ],
            shell_commands=[
                f"cd {geos}/experiment/1x6",
                "",
                "export FV3_DACEMODE=BuildAndRun",
                "export PACE_CONSTANTS=GEOS",
                "export PACE_FLOAT_PRECISION=32",
                "export PYTHONOPTIMIZE=1",
                "export PACE_LOGLEVEL=DEBUG",
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

        srun_script_fortran_name = "srun_script_fortran.sh"
        shell_script(
            name=srun_script_fortran_name.replace(".sh", ""),
            env_to_source=[
                "./setenv.sh",
            ],
            shell_commands=[
                f"cd {geos}/experiment/3x24",
                "",
                "srun --account=j1013 --constraint=rome \\",
                "     --qos=4n_a100 --partition=gpu_a100 \\",
                "     --nodes=2 --ntasks=72  \\",
                "     --ntasks-per-socket=24 --sockets-per-node=2 \\",
                "     --time=1:00:00 \\",
                "     --output=log.fortran.%t.out \\",
                f"     ./gpu-wrapper-slurm.sh ./{executable_name}",
            ],
            execute=False,
        )

        if action == PipelineAction.Validation or action == PipelineAction.All:
            # Run the simulation as-is: one 3 timesteps
            execute_shell_script(srun_script_gpu_name)

        if action == PipelineAction.Benchmark or action == PipelineAction.All:
            # Execute gtFV3
            _replace_in_file(
                srun_script_gpu_name,
                "--output=log.validation.%t.out",
                "--output=log.gtfv3.%t.out",
            )
            execute_shell_script(srun_script_gpu_name)

            # Execute Fortran
            execute_shell_script(srun_script_fortran_name)

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
                f"{geos_experiment_path}/1x6/log.validation.0.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.validation.1.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.validation.2.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.validation.3.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.validation.4.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.validation.5.out", artifact_directory
            )

        if action == PipelineAction.Benchmark or action == PipelineAction.All:
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.0.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.1.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.2.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.3.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.4.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/3x24/log.fortran.5.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.0.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.1.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.2.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.3.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.4.out", artifact_directory
            )
            shutil.copy(
                f"{geos_experiment_path}/1x6/log.gtfv3.5.out", artifact_directory
            )

        return True
