import os
from typing import Dict


class Environment:
    def __init__(self) -> None:
        self.vault: Dict[str, str] = {}

    def _get_from_osenv(self, key: str) -> str:
        if key not in self.vault.keys():
            self.vault[key] = os.getenv(key, "")
        return self.vault[key]

    def set(self, key: str, value: str):
        self.vault[key] = value

    def exists(self, key: str) -> bool:
        return key in self.vault.keys()

    def get(self, key: str) -> str:
        return self.vault[key]

    @property
    def CI_WORKSPACE(self):
        return self._get_from_osenv("CI_WORKSPACE")
