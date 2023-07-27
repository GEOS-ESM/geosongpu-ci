from typing import Dict, Any
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.actions.pipeline import PipelineAction


def git_prelude(
    config: Dict[str, Any],
    experiment_name: str,
    action: PipelineAction,
    metadata: Dict[str, Any],
    override_repo_name: str = "",
    do_mepo: bool = True,
) -> Dict[str, Any]:
    git_config = config["repository"]

    shell_script(
        name="setup_repository",
        modules=["other/mepo"],
        shell_commands=[
            f"git clone {git_config['url']} {override_repo_name}",
            f"cd {override_repo_name}",
            f"git checkout {git_config['tag_or_hash']}",
        ],
    )

    # Write metadata file
    if do_mepo:
        if "mepo" in git_config.keys() and "develop" in git_config["mepo"].keys():
            develop_comp_command = "mepo develop"
            for comp in git_config["mepo"]["develop"]:
                develop_comp_command += f" {comp}"
        else:
            develop_comp_command = ""
        mepo_status = shell_script(
            name="mepo_clone_and_status",
            modules=["other/mepo"],
            shell_commands=[
                f"cd {override_repo_name}",
                "mepo clone",
                develop_comp_command,
                "mepo status",
            ],
            temporary=True,
        )
        metadata["mepo_status"] = mepo_status
