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
        geos_install_path = env.get("GEOS_INSTALL")
        geos_build_path = f"{geos_install_path}/../build"
        
        # Copy input
        input_config = config["input"]
        shell_script(
            name="copy_input",
            modules=[],
            shell_commands=[
                f"cd {geos_build_path}",
                "mkdir experiment", 
                "cd experiment",
                f"cp -r {input_config['directory']}/* .",
                "rm ./setenv.sh",
            ],
        )

        # TODO: this SimpleAGCM.rc edit should be removed/altered when
        #       we will use proper data from /projects
        with open(f"{geos_build_path}/experiment/AgcmSimple.rc", "a") as f:
            f.write("RUN_GTFV3: 1\n")

        # Run
        geos_fvdycore_comp = f"{geos_install_path}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
        shell_script(
            name="setenv",
            shell_commands=[
                "echo \"Copy execurable GEOSgcm.x\"",
                "",
                f"cp {geos_install_path}/bin/GEOSgcm.x {geos_build_path}/experiment",
                "",
                "echo \"Loading env (g5modules & pyenv)\"",
                f"source {geos_install_path}/../@env/g5_modules.sh",
                f"VENV_DIR=\"{geos_fvdycore_comp}/geos-gtfv3/driver/setenv/gtfv3_venv\"",
                f"GTFV3_DIR=\"{geos_fvdycore_comp}/@gtFV3\"",
                f"GEOS_INSTALL_DIR=\"{geos_install_path}\"",
                f"source {geos_fvdycore_comp}/geos-gtfv3/driver/setenv/pyenv.sh",
            ],
            execute=False,
        )

        shell_script(
            name="srun_script",
            env_to_source=[
                "./setenv.sh",
            ],
            shell_commands=[
                f"cd {geos_build_path}/experiment",
                "",
                "export FV3_DACEMODE=BuildAndRun",
                "export PACE_CONSTANTS=GEOS",
                "export PACE_FLOAT_PRECISION=32",
                "export PYTHONOPTIMIZE=1",
                "",
                "srun --account=j1013 \\",
                "     --nodes=2 --ntasks=6 --ntasks-per-node=4 \\",
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
        geos_install_path = env.get("GEOS_INSTALL")
        geos_build_path = f"{geos_install_path}/../build"
        file_exists = os.path.isfile("ci_metadata")
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata. Coding or Permission error."
            )
        artifact_directory = f"{artifact_base_directory}/held_suarez/"
        os.mkdir(artifact_directory)
        shutil.copy("ci_metadata", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.0.out", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.1.out", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.2.out", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.3.out", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.4.out", artifact_directory)
        shutil.copy(f"{geos_build_path}/experiment/log.5.out", artifact_directory)

        return True
