from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.utils.shell import shell_script, execute_shell_script
from typing import Dict, Any
import shutil
import os
import glob


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
        geos_experiment_path = f"{geos_install_path}/../experiment"

        # Copy input
        input_config = config["input"]
        shell_script(
            name="copy_input",
            modules=[],
            shell_commands=[
                f"mkdir -p {geos_experiment_path}",
                f"cd {geos_experiment_path}",
                f"cp -R {input_config['directory']}/* .",
            ],
        )

        # Run sbatch in blocking mode
        # Input directory has the full setup
        shell_script(
            name="run_validation",
            modules=[],
            shell_commands=[
                f"cd {geos_experiment_path}",
                f"sbatch -W gcm_run.j",
            ],
        )

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
                "Aquaplanet run didn't write ci_metadata. Coding or Permission error."
            )
        artifact_directory = f"{artifact_base_directory}/held_suarez/"
        os.mkdir(artifact_directory)
        shutil.copy("ci_metadata", artifact_directory)

        slurm_outs = glob.glob(f"{geos_experiment_path}/slurm-*.out")
        for out in slurm_outs:
            shutil.copy(out, artifact_directory)

        return True
