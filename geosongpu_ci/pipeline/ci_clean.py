from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.pipeline.actions import PipelineAction
import glob
import shutil


@Registry.register
class CIClean(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
    ):
        worked_root_dir = glob.glob(f"{env.CI_WORKSPACE}/../../2023*")
        worked_dir = glob.glob(f"{env.CI_WORKSPACE}*")
        for d in worked_root_dir:
            print(f"Nuking {d}")
            shutil.rmtree(d, ignore_errors=False, onerror=None)
        for d in worked_dir:
            print(f"Nuking {d}")
            shutil.rmtree(d, ignore_errors=False, onerror=None)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        return True
