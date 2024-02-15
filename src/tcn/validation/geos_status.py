import dataclasses
from dataclasses import dataclass
from git import Repo
import yaml
import pathlib
from typing import List, Optional


@dataclass
class RepositoryStatus:
    name: str
    hexsha: str
    tag: Optional[str] = None


@dataclass
class GEOSStatus:
    repositories: List[RepositoryStatus] = dataclasses.field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GEOSStatus):
            raise ValueError("Need to == with another GEOSStatus")
        for r_status in self.repositories:
            # Check names & hashes
            if (
                len(
                    [
                        other_status.name
                        for other_status in other.repositories
                        if other_status.name == r_status.name
                        and other_status.hexsha == r_status.hexsha
                    ]
                )
                == 0
            ):
                return False

        return True


def _get_all_repo_status(
    mepo_components_path: str, verbose: bool = False
) -> GEOSStatus:
    geos_dir = pathlib.Path(mepo_components_path).parent.resolve()
    with open(mepo_components_path) as f:
        comps = yaml.safe_load(f)
    all_repos: List[RepositoryStatus] = []
    for comp, config in comps.items():
        if "local" in config.keys():
            r = Repo(f"{geos_dir}/{config['local']}")
            hexsha = r.head.commit.hexsha
            tag = None
            for t in r.tags:
                if t.commit.hexsha == hexsha:
                    tag = t.name
                    break
            tag_as_str = ""
            if tag:
                tag_as_str = f" (tag: {tag})"
            all_repos.append(RepositoryStatus(comp, r.head.commit.hexsha, tag_as_str))
            if verbose:
                print(f"{comp:<25}{r.head.commit.hexsha}{tag_as_str}")
    return GEOSStatus(all_repos)


if __name__ == "__main__":
    geos_mepo_components = "/home/fgdeconi/work/git/hs/geos/components.yaml"
    hs = _get_all_repo_status(geos_mepo_components, verbose=True)
    geos_mepo_components = "/home/fgdeconi/work/git/hs/geos/components.yaml"
    hs2 = _get_all_repo_status(geos_mepo_components, verbose=True)
    geos_mepo_components = "/home/fgdeconi/work/git/aq/geos/components.yaml"
    aq = _get_all_repo_status(geos_mepo_components, verbose=True)
    assert hs == hs2
    assert hs == aq
