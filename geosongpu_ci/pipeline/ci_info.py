from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.shell import ShellScript


@Registry.register
class CIInfo(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        super().__init__(skip_metadata=True)
        r = ShellScript("showquota").write(["showquota"]).execute()
        print(r)

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        return True
