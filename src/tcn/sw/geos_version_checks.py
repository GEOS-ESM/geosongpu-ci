import yaml
import urllib.request
from typing import Any, Dict, List

GEOSGCM_RAW_URL_UNFORMATTED = (
    "https://raw.githubusercontent.com/GEOS-ESM/GEOSgcm/{branch}/components.yaml"
)


def _compare_verb(A: Dict[str, Any], B: Dict[str, Any], verb: str, diff: List[Any]):
    for key, value in A.items():
        if key not in B.keys():
            continue
        if verb in value.keys() and (
            verb not in B[key].keys() or (value[verb] != B[key][verb])
        ):
            diff.append((key, verb, value[verb], B[key][verb]))


def compare(reference_branch: str, to_compare_branch: str):
    reference_yaml = GEOSGCM_RAW_URL_UNFORMATTED.format(branch=reference_branch)
    reference = yaml.safe_load(urllib.request.urlopen(reference_yaml))

    compare_yaml = GEOSGCM_RAW_URL_UNFORMATTED.format(branch=to_compare_branch)
    compare = yaml.safe_load(urllib.request.urlopen(compare_yaml))

    missing_component = []
    for key, value in reference.items():
        if key not in compare.keys():
            missing_component.append(key)

    diff_component: List[Any] = []
    _compare_verb(reference, compare, "tag", diff_component)
    _compare_verb(reference, compare, "branch", diff_component)
    diff_develop: List[Any] = []
    _compare_verb(reference, compare, "develop", diff_develop)

    print(f"Missing components: {missing_component}")
    print("Different tag or branch:")
    for key, verb, vref, vcomp in diff_component:
        print(f"  {key}.{verb}: {vref} vs {vcomp}")
    print("Different develop:")
    for key, verb, vref, vcomp in diff_develop:
        print(f"  {key}.{verb}: {vref} vs {vcomp}")


if __name__ == "__main__":
    compare("main", "dsl/develop")
