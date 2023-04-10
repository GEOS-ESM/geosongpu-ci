import os


class Environment:
    def __init__(self) -> None:
        self.vault = {}

    def _get_from_osenv(self, key: str):
        if key not in self.vault.keys():
            self.vault[key] = os.getenv(key)
        return self.vault[key]

    def set(self, key: str, value: str):
        self.vault[key] = value

    def exists(self, key: str):
        return key in self.vault.keys()

    @property
    def CI_WORKSPACE(self):
        return self._get_from_osenv("CI_WORKSPACE")
