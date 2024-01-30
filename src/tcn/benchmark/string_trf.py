import re
from typing import List

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
