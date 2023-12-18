import os
import site
import sys


def find_template(name: str) -> str:
    # pip install geosongpu-ci
    candidate = f"{sys.prefix}/geosongpu/templates/{name}.tpl"
    if os.path.isfile(candidate):
        return candidate
    # pip install --user geosongpu-ci
    candidate = f"{site.USER_BASE}/geosongpu/templates/{name}.tpl"
    if os.path.isfile(candidate):
        return candidate
    # pip install -e geosongpu-ci
    candidate = os.path.join(
        os.path.dirname(__file__),
        f"{name}.tpl",
    )
    if os.path.isfile(candidate):
        return candidate
    raise FileNotFoundError(f"Template: could not locate {name}")
