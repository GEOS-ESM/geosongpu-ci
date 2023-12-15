class CICheckException(Exception):
    "Exception raised when Check action fails"

    def __init__(self, message):
        super().__init__(f"[CI Check failure] {message}")
