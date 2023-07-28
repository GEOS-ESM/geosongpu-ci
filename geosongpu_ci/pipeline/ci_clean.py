from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.actions.pipeline import PipelineAction
import shutil
from os.path import abspath
from os import mkdir
from geosongpu_ci.utils.shell import ShellScript


@Registry.register
class CIClean(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        super().__init__(skip_metadata=True)
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
        artifact_dir = abspath(f"{env.CI_WORKSPACE}/../")
        shutil.rmtree(artifact_dir, ignore_errors=False, onerror=None)
        mkdir(artifact_dir)
        return True


@Registry.register
class SlurmCancelJob(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Build GEOS
        ShellScript("cancel_slurm_jobs").write(["scancel -u gmao_ci"]).execute()

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        return True
