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
            name="wip",
            modules=[],
            env_to_source=[],
            shell_commands=[
                "srun -A j1013 --qos=4n_a100 --partition=gpu_a100 --nodes=2 --ntasks=6 --ntasks-per-node=3 --gpus-per-node=3 --sockets-per-node=2 --mem-per-gpu=40G --output=log.%t.out nvidia-smi",
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
