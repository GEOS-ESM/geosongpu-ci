from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.pipeline.actions import PipelineAction
import datetime
import os
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
    ) -> bool:
        return os.path.isfile("ci_metadata")
