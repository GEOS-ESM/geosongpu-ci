import datetime
import os
import site
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable

import yaml

from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.utils.environment import Environment
from tcn.ci.utils.progress import Progress
from tcn.ci.utils.registry import Registry


class TaskBase(ABC):
    """Assume we are in CI_WORKSPACE - ready to execute"""

    def __init__(self, skip_metadata=False) -> None:
        super().__init__()
        self.skip_metadata = skip_metadata

    def _prelude(self, config: Dict[str, Any], env: Environment):
        env.metadata["timestamp"] = str(datetime.datetime.now())
        env.metadata["config"] = {"name": env.experiment_name, "value": config}
        env.metadata["action"] = str(env.experiment_action)

    def _dump_metadata(self, env: Environment):
        with open("ci_metadata", "w") as f:
            yaml.dump(env.metadata, f)

    def run(
        self,
        config: Dict[str, Any],
        env: Environment,
    ):
        self._prelude(config, env)
        self.run_action(config, env)
        if not self.skip_metadata:
            self._dump_metadata(env)

    @abstractmethod
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
    ):
        ...

    @abstractmethod
    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        ...

    @staticmethod
    def step_options() -> Iterable[str]:
        return ["all", "run", "check"]


def _find_experiments() -> str:
    # pip install smtn
    candidate = f"{sys.prefix}/smtn/ci_experiments/experiments.yaml"
    if os.path.isfile(candidate):
        return candidate
    # pip install --user smtn
    candidate = f"{site.USER_BASE}/smtn/ci_experiments/experiments.yaml"
    if os.path.isfile(candidate):
        return candidate
    # pip install -e smtn
    candidate = os.path.join(
        os.path.dirname(__file__), "../../ci_experiments/experiments.yaml"
    )
    if os.path.isfile(candidate):
        return candidate
    raise RuntimeError("Cannot find experiments.yaml")


def get_config(experiment_name: str) -> Dict[str, Any]:
    experiment_path = _find_experiments()
    with open(experiment_path) as f:
        configurations = yaml.safe_load(f)
    if experiment_name not in configurations.keys():
        raise RuntimeError(f"Experiment {experiment_name} is unknown")
    return configurations[experiment_name]


def dispatch(
    experiment_name: str,
    experiment_action: PipelineAction,
    artifact_directory: str,
    setup_only: bool = False,
):
    # Get config
    config = get_config(experiment_name)

    # Build environment
    metadata: Dict[str, Any] = {}
    env = Environment(
        experience_name=experiment_name,
        experiment_action=experiment_action,
        artifact_directory=artifact_directory,
        setup_only=setup_only,
        metadata=metadata,
    )

    # Run pipeline
    with Progress(f"Pipeline for experiment {experiment_name}"):
        for task in config["tasks"]:
            t = Registry.registry[task]()
            with Progress(f"{task}.run for {experiment_action}"):
                t.run(config, env)
            if not setup_only:
                with Progress(f"{task}.check for {experiment_action}"):
                    check = t.check(
                        config,
                        env,
                    )
                    if not check:
                        raise RuntimeError(
                            f"Check for {task} failed for {experiment_action}"
                        )
            else:
                Progress.log(
                    f"= = = Skipping {task}.check for {experiment_action} = = ="
                )
