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
        ShellScript("showquota").write(
            [
                "showquota",
                "cd /discover/nobackup/gmao_ci/",
                "du -a | cut -d/ -f2 | sort | uniq -c | sort -nr",
            ]
        ).execute()

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        return True
