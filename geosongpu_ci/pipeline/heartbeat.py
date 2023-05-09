from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.actions.pipeline import PipelineAction
import datetime
import os
import shutil
import yaml


@Registry.register
class Heartbeat(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        pass

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        if env.CI_WORKSPACE == "":
            raise RuntimeError("Environment error: CI_WORKSPACE is not set.")
        print(f"CI_WORKSPACE: {env.CI_WORKSPACE}")

        if action == PipelineAction.All or action == PipelineAction.Validation:
            file_exists = os.path.isfile("ci_metadata")
            if not file_exists:
                raise RuntimeError(
                    "Heartbeat.run didn't write ci_metadata. Coding or Permission error."
                )
            artifact_directory = f"{artifact_base_directory}/ci-heartbeat/"
            os.mkdir(artifact_directory)
            shutil.copy("ci_metadata", artifact_directory)
            print(f"Heartbeart w/ {action} expect success & artifact saved.")
            return True
        else:
            print(f"Heartbeart w/ {action} expect failure")
            return False
