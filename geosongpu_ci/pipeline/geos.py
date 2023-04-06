from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.pipeline.actions import PipelineAction
import datetime
import yaml


@Registry.register
class GEOS(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
    ):
        git_config = config["repository"]

        shell_script(
            name="setup_repository",
            modules=["other/mepo"],
            shell_commands=[
                f"git clone {git_config['url']} geos",
                f"cd geos",
                f"git checkout {git_config['tag_or_hash']}",
                f"mepo clone",
            ],
        )

        mepo_status = shell_script(
            name="get_mepo_status",
            modules=["other/mepo"],
            shell_commands=[
                f"mepo status",
            ],
            temporary=True,
        )

        # Write metadata file
        with open("ci_metadata", "w") as f:
            metadata = {}
            metadata["timestamp"] = str(datetime.datetime.now())
            metadata["config"] = {"name": experiment_name, "value": config}
            metadata["action"] = str(action)
            metadata["mepo_status"] = mepo_status
            yaml.dump(metadata, f)

        # Build GEOS
        shell_script(
            name="build_geos",
            modules=[],
            env_to_source="geos/@env/g5_modules.sh",
            shell_commands=[
                f"cd geos",
                f"mkdir build",
                f"cd build",
                f"cmake .. -DBASEDIR=$BASEDIR/Linux -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_INSTALL_PREFIX=../install"
                f"make -j24 GEOSgcm.x",
            ],
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
    ) -> bool:
        return True
