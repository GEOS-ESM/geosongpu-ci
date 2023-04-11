from geosongpu_ci.utils.environment import Environment
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
        env: Environment,
    ):
        git_config = config["repository"]

        shell_script(
            name="setup_repository",
            modules=["other/mepo"],
            shell_commands=[
                f"git clone {git_config['url']} geos",
                "cd geos",
                f"git checkout {git_config['tag_or_hash']}",
                "mepo clone",
            ],
        )

        # Write metadata file
        mepo_status = shell_script(
            name="get_mepo_status",
            modules=["other/mepo"],
            shell_commands=[
                "cd geos",
                "mepo status",
            ],
            temporary=True,
        )
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
            env_to_source=[
                "geos/@env/g5_modules.sh",
            ],
            shell_commands=[
                "cd geos",
                "mkdir build",
                "cd build",
                f"export TMP={env.CI_WORKSPACE}/geos/build/tmp",
                "export TMPDIR=$TMP",
                "export TEMP=$TMP",
                "mkdir $TMP",
                "echo $TMP",
                "cmake .. -DBASEDIR=$BASEDIR/Linux -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_INSTALL_PREFIX=../install",
                "make -j12",
            ],
        )

        # Export GEOS_INSTALL for future scripts
        env.set(
            "GEOS_INSTALL",
            f"{env.CI_WORKSPACE}/geos/GEOSgcm/held-suarez/hs-oacc-gtfv3",
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return env.exists("GEOS_INSTALL")
