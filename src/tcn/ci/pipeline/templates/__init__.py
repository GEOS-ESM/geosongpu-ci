import os
import site
import sys


def find_template(name: str) -> str:
    # pip install smtn
    candidate = f"{sys.prefix}/smtn/templates/{name}.tpl"
    if os.path.isfile(candidate):
        return candidate
    # pip install --user smtn
    candidate = f"{site.USER_BASE}/smtn/templates/{name}.tpl"
    if os.path.isfile(candidate):
        return candidate
    # pip install -e smtn
    candidate = os.path.join(
        os.path.dirname(__file__),
        f"{name}.tpl",
    )
    if os.path.isfile(candidate):
        return candidate
    raise FileNotFoundError(f"Template: could not locate {name}")
