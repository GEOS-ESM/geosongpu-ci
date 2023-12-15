import time


class Progress:
    """Progress and log to track"""

    def __init__(self, title: str):
        self.title = title

    @classmethod
    def default_prefix(cls) -> str:
        return "[GEOSONGPU]:"

    @classmethod
    def log(cls, msg):
        print(cls.default_prefix(), msg)

    def __enter__(self):
        self.start = time.time()
        Progress.log(f"Running {self.title} ...")

    def __exit__(self, _type, _val, _traceback):
        elapsed = time.time() - self.start
        Progress.log(f"...{elapsed:.2f}s ({self.title}).")
