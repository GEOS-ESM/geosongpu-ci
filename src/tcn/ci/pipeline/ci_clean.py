import shutil
from os import mkdir
from os.path import abspath
from typing import Any, Dict

from tcn.ci.pipeline.task import TaskBase
from tcn.ci.utilsenvironment import Environment
from tcn.ci.utilsregistry import Registry
from tcn.ci.utilsshell import ShellScript


@Registry.register
class CIClean(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
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
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Build GEOS
        ShellScript("cancel_slurm_jobs").write(["scancel -u gmao_ci"]).execute()

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        return True
