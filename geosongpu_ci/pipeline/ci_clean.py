from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.pipeline.actions import PipelineAction
import glob
import shutil
from os.path import abspath
from os import mkdir


@Registry.register
class CIClean(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
    ):
        work_dir = abspath(f"{env.CI_WORKSPACE}/../")
        shutil.rmtree(f"{work_dir}", ignore_errors=False, onerror=None)
        mkdir(f"{work_dir}")
        mkdir(f"{env.CI_WORKSPACE}")

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        return True
