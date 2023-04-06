from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from actions import PipelineAction
import datetime
import os


@Registry.register
class Heartbeat(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
    ):
        # Write metadata file
        with open("ci_metadata") as f:
            metadata = {}
            metadata["timestamp"] = str(datetime.datetime.now())
            metadata["config"] = {"name": experiment_name, "value": config}
            metadata["action"] = str(action)
            f.write(metadata)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
    ) -> bool:
        return os.path.isfile("ci_metadata")
