import os
import shutil
from typing import Any, Dict

from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.pipeline.task import TaskBase
from tcn.ci.utilsenvironment import Environment
from tcn.ci.utilsregistry import Registry


@Registry.register
class Heartbeat(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        pass

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        if env.CI_WORKSPACE == "":
            raise RuntimeError("Environment error: CI_WORKSPACE is not set.")
        print(f"CI_WORKSPACE: {env.CI_WORKSPACE}")

        if (
            env.experiment_action == PipelineAction.All
            or env.experiment_action == PipelineAction.Validation
        ):
            file_exists = os.path.isfile("ci_metadata")
            if not file_exists:
                raise RuntimeError(
                    "Heartbeat.run didn't write ci_metadata. "
                    "Coding or Permission error."
                )
            artifact_directory = f"{env.artifact_directory}/ci-heartbeat/"
            os.mkdir(artifact_directory)
            shutil.copy("ci_metadata", artifact_directory)
            print(
                f"Heartbeart w/ {env.experiment_action} "
                "expect success & artifact saved."
            )
            return True
        else:
            print(f"Heartbeart w/ {env.experiment_action} expect failure")
            return False
