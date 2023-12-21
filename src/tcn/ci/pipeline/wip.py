from typing import Any, Dict

from tcn.ci.pipeline.task import TaskBase
from tcn.ci.utils.environment import Environment
from tcn.ci.utils.registry import Registry
from tcn.ci.utils.shell import ShellScript


@Registry.register
class WIP(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Build GEOS
        ShellScript(name="wip").write(
            modules=[],
            env_to_source=[],
            shell_commands=[
                "srun -A j1013 -C rome --qos=4n_a100 --partition=gpu_a100 --nodes=2 --ntasks=6 --ntasks-per-node=3 --gpus-per-node=3 --sockets-per-node=2 --mem-per-gpu=40G --output=log.%t.out nvidia-smi",
            ],
        ).execute()

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        return True
