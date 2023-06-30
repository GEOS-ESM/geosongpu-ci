from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.pipeline.geos import (
    make_gpu_wrapper_script,
    copy_input_from_project,
    set_python_environment,
    make_srun_script,
)
from geosongpu_ci.utils.shell import execute_shell_script
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
class Aquaplanet(TaskBase):
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

        make_gpu_wrapper_script(geos, layout)

        # TODO: cache build to not BuildAndRun all the time
        # TODO: mepo hash as a combination of all the hashes

        executable_name = "GEOSgcm.x"
        set_python_environment(geos_install_path, executable_name, geos)

        srun_script_gpu_name = make_srun_script(geos, executable_name, layout)

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
