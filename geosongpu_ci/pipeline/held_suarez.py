from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.pipeline.actions import PipelineAction
from geosongpu_ci.utils.shell import shell_script
from typing import Dict, Any
import shutil
import os


@Registry.register
class HeldSuarez(TaskBase):
    def run(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
    ):
        # Copy input
        input_config = config["input"]
        shell_script(
            name="copy_input",
            modules=[],
            shell_commands=[
                "cd ./geos/build",
                "mkdir experiment",
                "cd experiment",
                f"cp -r {input_config['directory']}/* .",
                "rm ./setenv.sh",
            ],
        )

        # Run
        shell_script(
            name="setenv.sh",
            shell_commands=[
                f"GEOS_INSTALL_DIR={env.get('GEOS_INSTALL')}/install/release/gtfv3/cuda11.2.2-gcc10.4.0nvptx-openmpi4.1.4",
                "",
                "GEOSBIN=$GEOS_INSTALL_DIR/bin",
                "GEOSLIB=$GEOS_INSTALL_DIR/lib",
                "",
                "cp $GEOSBIN/GEOSgcm.x .",
                "",
                "source $GEOSBIN/g5_modules.sh",
                "export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${BASEDIR}/$(uname)/lib:${GEOSLIB}",
                "",
                "export PYTHONPATH=${GEOSDIR}/src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/geos-gtfv3",
                "GTFV3=${GEOSDIR}/src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/@gtfv3",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/dsl",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/util",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/driver",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/physics",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/fv3core",
                "export PYTHONPATH=${PYTHONPATH}:${GTFV3}/stencils",
            ],
            execute=False,
        )

        shell_script(
            name="srun_script",
            env_to_source=[
                "geos/@env/g5_modules.sh",
                "setenv.sh",
            ],
            shell_commands=[
                "#!/usr/bin/bash",
                "",
                "cd ./geos/build/experiment",
                "",
                "srun --nodes=2 --ntasks=6 --ntasks-per-node=4 \\",
                "     --ntasks-per-socket=2 --gpus-per-node=4 \\",
                "     --sockets-per-node=2 --gpus-per-socket=2 \\",
                "     --gpus-per-task=1 --constraint=rome \\",
                "     --partition=gpu_a100 --qos=4n_a100 \\",
                "     --time=12:00:00 \\",
                "     --output=log.%t.out \\",
                "     ./gpu-wrapper-ompi.sh ./GEOSgcm.x",
            ],
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        file_exists = os.path.isfile("ci_metadata")
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata. Coding or Permission error."
            )
        artifact_directory = f"{artifact_base_directory}/held_suarez/"
        os.mkdir(artifact_directory)
        shutil.copy("ci_metadata", artifact_directory)
        shutil.copy("log.0.out", artifact_directory)
        shutil.copy("log.1.out", artifact_directory)
        shutil.copy("log.2.out", artifact_directory)
        shutil.copy("log.3.out", artifact_directory)
        shutil.copy("log.4.out", artifact_directory)
        shutil.copy("log.5.out", artifact_directory)

        return True
