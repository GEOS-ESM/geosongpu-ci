
from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.pipeline.actions import PipelineAction
import shutil
from os.path import abspath
from os import mkdir
from geosongpu_ci.utils.shell import shell_script

@Registry.register
class WIP(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
    ):
        # Build GEOS
        shell_script(
            name="cancel_slurm_jobs",
            modules=[],
            env_to_source=[],
            shell_commands=[
                "echo `id`",
                # "ls /discover/nobackup/projects/geosongpu/geos_data/held_suarez/C12-L91",
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
        return True
