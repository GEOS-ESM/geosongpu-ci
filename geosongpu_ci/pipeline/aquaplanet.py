from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.slurm import wait_for_sbatch
from geosongpu_ci.pipeline.geos import copy_input_from_project
from geosongpu_ci.utils.shell import shell_script
from typing import Dict, Any


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

        experiment_dir = copy_input_from_project(config, geos, layout)
        _replace_in_file(
            url=f"{experiment_dir}/gcm_run.j",
            text_to_replace="setenv GEOSBASE TO_BE_REPLACED",
            new_text=f"setenv GEOSBASE {geos}",
        )
        _replace_in_file(
            url=f"{experiment_dir}/gcm_run.j",
            text_to_replace="setenv EXPDIR TO_BE_REPLACED",
            new_text=f"setenv EXPDIR {experiment_dir}",
        )

        run_script_gpu_name = "run_script_gpu.sh"
        sbatch_result = shell_script(
            name=run_script_gpu_name.replace(".sh", ""),
            env_to_source=[],
            shell_commands=[
                f"cd {experiment_dir}",
                "sbatch gcm_run.j",
            ],
        )
        wait_for_sbatch(sbatch_result.split(" ")[-1].strip().replace("\n", ""))

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        # TODO
        return True
