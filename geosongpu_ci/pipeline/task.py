from typing import Dict, Any
from geosongpu_ci.pipeline.actions import PipelineAction
import sys
import site
import os
import yaml
from abc import ABC, abstractmethod
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.utils.environment import Environment


class TaskBase(ABC):
    """Assume we are in CI_WORKSPACE - ready to execute"""

    @abstractmethod
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
    ):
        ...

    @abstractmethod
    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        ...


def _find_experiments() -> str:
    # pip install geosongpu-ci
    candidate = f"{sys.prefix}/geosongpu/experiments/experiments.yaml"
    if os.path.isfile(candidate):
        return candidate
    # pip install --user geosongpu-ci
    candidate = f"{site.USER_BASE}/geosongpu/experiments/experiments.yaml"
    if os.path.isfile(candidate):
        return candidate
    # pip install -e geosongpu-ci
    candidate = os.path.join(
        os.path.dirname(__file__), "../../experiments/experiments.yaml"
    )
    if os.path.isfile(candidate):
        return candidate
    raise RuntimeError("Cannot find experiments.yaml")


def dispatch(
    experiment_name: str,
    experiment_action: PipelineAction,
    artifact_directory: str,
):
    # Get config
    experiment_path = _find_experiments()
    with open(experiment_path) as f:
        configurations = yaml.safe_load(f)
    if experiment_name not in configurations.keys():
        raise RuntimeError(f"Experiment {experiment_name} is unknown")
    config = configurations[experiment_name]

    # Build environment
    env = Environment()

    # Run pipeline
    for task in config["tasks"]:
        t = Registry.registry[task]()
        print(f"> > > {task}.run for {experiment_action}")
        t.run(config, experiment_name, experiment_action, env)
        print(f"> > > {task}.check for {experiment_action}")
        check = t.check(
            config,
            experiment_name,
            experiment_action,
            artifact_directory,
            env,
        )
        if check == False:
            raise RuntimeError(f"Check for {task} failed for {experiment_action}")
