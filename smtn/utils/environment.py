import os
from typing import Dict
from smtn.actions.pipeline import PipelineAction


class Environment:
    """Transparently store cli options, evironement variable and any
    variables the tasks exchange between them"""

    def __init__(
        self,
        experience_name: str,
        experiment_action: PipelineAction,
        artifact_directory: str,
        setup_only: bool,
    ) -> None:
        self.vault: Dict[str, str] = {}
        self.setup_only = setup_only
        self.experiment_name = experience_name
        self.experiment_action = experiment_action
        self.artifact_directory = artifact_directory

    def set(self, key: str, value: str):
        self.vault[key] = value

    def exists(self, key: str) -> bool:
        return key in self.vault.keys()

    def get(self, key: str) -> str:
        if key not in self.vault.keys():
            self.vault[key] = os.getenv(key, "")
        return self.vault[key]

    @property
    def CI_WORKSPACE(self):
        return self.get("CI_WORKSPACE")
