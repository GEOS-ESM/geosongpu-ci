import re
from typing import List, Optional

_numeric_const_pattern = (
    "[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?"  # noqa
)
RE_NUMERIC = re.compile(_numeric_const_pattern, re.VERBOSE)


def extract_numerics(strings: List[str]) -> List[float]:
    results = []
    for s in strings:
        for r in RE_NUMERIC.findall(s):
            results.append(r)

    return [float(r) for r in results]


def grep(
    filename: str,
    pattern: str,
    exclude_pattern: Optional[bool] = False,
    start_patterns: Optional[List[str]] = None,
    end_pattern: Optional[str] = None,
    expected: Optional[bool] = True,
    starts_with: bool = False,
) -> List[str]:
    results = []
    spatterns = start_patterns.copy() if start_patterns else None
    start_pattern = spatterns.pop(0) if spatterns else None
    with open(filename, "r") as f:
        for line in f.readlines():
            if start_pattern and start_pattern and start_pattern in line:
                if spatterns != []:
                    start_pattern = spatterns.pop(0) if spatterns else None
                else:
                    start_pattern = None
            if end_pattern and end_pattern in line:
                break
            if not start_pattern and pattern in line:
                if exclude_pattern and starts_with and line.startswith(pattern):
                    line = "".join(line.split(pattern)[1:])
                elif exclude_pattern and pattern in line:
                    line = "".join(line.split(pattern)[1:])
                if line != "":
                    results.append(line)
    if expected and results == []:
        raise RuntimeError(f"Expecting {pattern} to be found")
    return results
