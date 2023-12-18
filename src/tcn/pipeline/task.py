from typing import Dict, Any, Iterable
from tcn.actions.pipeline import PipelineAction
import sys
import site
import os
import yaml
from abc import ABC, abstractmethod
from tcn.utils.registry import Registry
from tcn.utils.environment import Environment
from tcn.utils.progress import Progress
import datetime


class TaskBase(ABC):
    """Assume we are in CI_WORKSPACE - ready to execute"""

    def __init__(self, skip_metadata=False) -> None:
        super().__init__()
        self.metadata = {}
        self.skip_metadata = skip_metadata

    def _prelude(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
    ) -> Dict[str, Any]:
        self.metadata["timestamp"] = str(datetime.datetime.now())
        self.metadata["config"] = {"name": experiment_name, "value": config}
        self.metadata["action"] = str(action)

    def _dump_metadata(self):
        with open("ci_metadata", "w") as f:
            yaml.dump(self.metadata, f)

    def run(
        self,
        config: Dict[str, Any],
        env: Environment,
    ):
        self._prelude(
            config=config,
            experiment_name=env.experiment_name,
            action=env.experiment_action,
        )
        self.run_action(
            config=config,
            env=env,
            metadata=self.metadata,
        )
        if not self.skip_metadata:
            self._dump_metadata()

    @abstractmethod
    def run_action(
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
        env: Environment,
    ) -> bool:
        ...

    @staticmethod
    def step_options() -> Iterable[str]:
        return ["all", "run", "check"]


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
    env = Environment(
        experience_name=experiment_name,
        experiment_action=experiment_action,
        artifact_directory=artifact_directory,
        setup_only=setup_only,
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
