from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.pipeline.actions import PipelineAction
import datetime
import os
import shutil
import yaml


@Registry.register
class Heartbeat(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
    ):
        # Write metadata file
        with open("ci_metadata", "w") as f:
            metadata = {}
            metadata["timestamp"] = str(datetime.datetime.now())
            metadata["config"] = {"name": experiment_name, "value": config}
            metadata["action"] = str(action)
            yaml.dump(metadata, f)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
    ) -> bool:
        if action == PipelineAction.All or action == PipelineAction.Validation:
            file_exists = os.path.isfile("ci_metadata")
            if not file_exists:
                raise RuntimeError("Heartbeat.run didn't write ci_metadata. Coding or Permission error.")
            artifact_directory = f"{artifact_base_directory}/ci-heartbeat/"
            os.mkdir(artifact_directory)
            shutil.copy("ci_metadata", artifact_directory)
            print(f"Heartbeart w/ {action} expect success & artifact saved.")
            return True
        else:
            print(f"Heartbeart w/ {action} expect failure")
            return False
