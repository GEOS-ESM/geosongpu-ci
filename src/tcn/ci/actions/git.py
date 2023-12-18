from typing import Any, Dict

from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.utilsshell import ShellScript


def git_prelude(
    config: Dict[str, Any],
    experiment_name: str,
    action: PipelineAction,
    metadata: Dict[str, Any],
    override_repo_name: str = "",
    do_mepo: bool = True,
) -> None:
    git_config = config["repository"]
    modules = []

    # Basic git commands to clone/checkout the repository
    git_commands = [
        f"git clone {git_config['url']} {override_repo_name}",
        f"cd {override_repo_name}",
        f"git checkout {git_config['tag_or_hash']}",
    ]

    # Add the mepo commands to be triggered in the repository
    if do_mepo:
        if "mepo" in git_config.keys() and "develop" in git_config["mepo"].keys():
            develop_comp_command = "mepo develop"
            for comp in git_config["mepo"]["develop"]:
                develop_comp_command += f" {comp}"
        else:
            develop_comp_command = ""
        modules.append("other/mepo")
        git_commands.extend(
            [
                "mepo clone",
                develop_comp_command,
            ]
        )

    # Setup script
    ShellScript(f"checkout_repository_{experiment_name}").write(
        modules=modules,
        shell_commands=git_commands,
    ).execute()
