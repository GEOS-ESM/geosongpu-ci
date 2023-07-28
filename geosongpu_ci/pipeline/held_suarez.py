from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.slurm import SlurmConfiguration
from geosongpu_ci.utils.shell import ShellScript
from geosongpu_ci.pipeline.geos import set_python_environment
from geosongpu_ci.utils.progress import Progress
from typing import Dict, Any, Optional
import shutil
import os
import dataclasses
import glob


class PrologScripts:
    def __init__(
        self,
        experiment_directory: str,
        executable_name: str,
        geos_directory: str,
        geos_install_path: str,
    ):
        self._make_gpu_wrapper_script(experiment_directory=experiment_directory)
        self.set_env = set_python_environment(
            geos_directory=geos_directory,
            geos_install_dir=geos_install_path,
            working_directory=experiment_directory,
        )
        self._copy_executable_script(
            executable_name,
            experiment_directory,
            geos_install_path,
        )

    def _make_gpu_wrapper_script(self, experiment_directory: str) -> None:
        self.gpu_wrapper = ShellScript(
            "gpu-wrapper-slurm",
            working_directory=experiment_directory,
        ).write(
            modules=[],
            shell_commands=[
                "#!/usr/bin/env sh",
                "export CUDA_VISIBLE_DEVICES=$SLURM_LOCALID",
                'echo "Node: $SLURM_NODEID | Rank: $SLURM_PROCID,'
                ' pinned to GPU: $CUDA_VISIBLE_DEVICES"',
                "$*",
            ],
        )

    def _copy_executable_script(
        self,
        executable_name: str,
        experiment_directory: str,
        geos_install_path: str,
    ) -> None:
        self.copy_executable = ShellScript(
            "copy_executable",
            working_directory=experiment_directory,
        )
        self.copy_executable.write(
            shell_commands=[
                f'echo "Copy executable {executable_name}"',
                "",
                f"cp {geos_install_path}/bin/{executable_name} {experiment_directory}",
            ],
        )


@dataclasses.dataclass
class GTFV3Config:
    FV3_DACEMODE: str = "BuildAndRun"
    PACE_CONSTANTS: str = "GEOS"
    PACE_FLOAT_PRECISION: int = 32
    PACE_LOGLEVEL: str = "DEBUG"
    GTFV3_BACKEND: str = "dace:gpu"

    def sh(self) -> str:
        return (
            f"export FV3_DACEMODE={self.FV3_DACEMODE}\n"
            f"export PACE_CONSTANTS={self.PACE_CONSTANTS}\n"
            f"export PACE_FLOAT_PRECISION={self.PACE_FLOAT_PRECISION}\n"
            f"export PACE_LOGLEVEL={self.PACE_LOGLEVEL}\n"
            f"export GTFV3_BACKEND={self.GTFV3_BACKEND}\n"
        )


def _copy_input_to_experiment_directory(
    input_directory: str,
    geos_directory: str,
    resolution: str,
    experiment_name: Optional[str] = None,
) -> str:
    """Copy the input directory into the experiment direcotry
    and trigger the "reset.sh" to get data clean and ready to execute.
    """
    if experiment_name:
        experiment_dir = f"{geos_directory}/experiment/{experiment_name}"
    else:
        experiment_dir = f"{geos_directory}/experiment/{resolution}"
    ShellScript(f"copy_input_{resolution}").write(
        modules=[],
        shell_commands=[
            f"cd {geos_directory}",
            f"mkdir -p {experiment_dir}",
            f"cd {experiment_dir}",
            f"cp -r {input_directory}/* .",
            "./reset.sh",
        ],
    ).execute()
    return experiment_dir


def _make_srun_script(
    executable_name: str,
    experiment_directory: str,
    slurm_config: SlurmConfiguration,
    gtfv3_config: GTFV3Config,
    prolog_scripts: PrologScripts,
) -> ShellScript:
    srun_cmd = slurm_config.srun_bash(
        wrapper=prolog_scripts.gpu_wrapper.path,
        executable_name=executable_name,
    )
    srun_script_script = ShellScript(
        f"srun_{slurm_config.ntasks}tasks",
        working_directory=experiment_directory,
    ).write(
        env_to_source=[
            prolog_scripts.set_env,
        ],
        shell_commands=[
            f"cd {experiment_directory}",
            "./reset.sh",
            f"source {prolog_scripts.copy_executable.path}",
            "",
            f"{gtfv3_config.sh()}",
            "export PYTHONOPTIMIZE=1",
            f"export CUPY_CACHE_DIR={experiment_directory}/.cupy",
            "",
            f"{srun_cmd}",
        ],
    )
    return srun_script_script


SLURM_One_Half_Nodes_GPU = SlurmConfiguration(
    nodes=2,
    ntasks=6,
    ntasks_per_node=3,
    sockets_per_node=2,
    gpus_per_node=3,
    mem_per_gpu="40G",
)
SLURM_One_Half_Nodes_CPU = SlurmConfiguration(
    nodes=2,
    ntasks=72,
    ntasks_per_node=48,
    sockets_per_node=2,
)

GTFV3_DaCeGPU_Orchestrated_32bit = GTFV3Config()

VALIDATION_RESOLUTION = "C180-L72"


@Registry.register
class HeldSuarez(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Setup
        geos_install_path = env.get("GEOS_INSTALL_DIRECTORY")
        geos = env.get("GEOS_BASE_DIRECTORY")
        executable_name = "./GEOShs.x"

        # # # Validation # # #
        if (
            env.experiment_action == PipelineAction.Validation
            or env.experiment_action == PipelineAction.All
        ):
            # Get experiment directory ready
            print(f"> > > Validation @ {VALIDATION_RESOLUTION}")
            experiment_dir = _copy_input_to_experiment_directory(
                input_directory=config["input"][VALIDATION_RESOLUTION],
                geos_directory=geos,
                resolution=VALIDATION_RESOLUTION,
            )
            prolog_scripts = PrologScripts(
                experiment_directory=experiment_dir,
                executable_name=executable_name,
                geos_directory=geos,
                geos_install_path=geos_install_path,
            )

            # Run 1 timestep for cache build
            slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_GPU)
            slurm_config.output = "validation.cache.dacegpu.%t.out"
            srun_script = _make_srun_script(
                executable_name=executable_name,
                experiment_directory=experiment_dir,
                slurm_config=slurm_config,
                gtfv3_config=GTFV3_DaCeGPU_Orchestrated_32bit,
                prolog_scripts=prolog_scripts,
            )
            ShellScript(
                name="setup_config_1ts_1node_gtfv3",
                working_directory=experiment_dir,
            ).write(
                shell_commands=[
                    f"cd {experiment_dir}",
                    "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                    "cp -f input.nml.1x1 input.nml",
                    "cp -f CAP.rc.1ts CAP.rc",
                ],
            ).execute()
            if not env.setup_only:
                srun_script.execute()

            # TODO: more to be done to actually check on the results rather then
            # just "can run".

        # # # Benchmark # # #
        if (
            env.experiment_action == PipelineAction.Benchmark
            or env.experiment_action == PipelineAction.All
        ):
            # We run a range of resolution. C180-L72 might already be ran
            for resolution in ["C180-L72", "C180-L91", "C180-L137"]:
                print(f"> > > Benchmark @ {resolution}")
                if (
                    resolution == VALIDATION_RESOLUTION
                    and env.experiment_action == PipelineAction.All
                ):
                    # In case validation ran already, we have the experiment dir
                    # and the cache ready to run
                    experiment_dir = f"{geos}/experiment/{resolution}"
                    prolog_scripts = PrologScripts(
                        experiment_directory=experiment_dir,
                        executable_name=executable_name,
                        geos_directory=geos,
                        geos_install_path=geos_install_path,
                    )
                else:
                    # Get experiment directory ready
                    experiment_dir = _copy_input_to_experiment_directory(
                        input_directory=config["input"][resolution],
                        geos_directory=geos,
                        resolution=resolution,
                    )
                    prolog_scripts = PrologScripts(
                        experiment_directory=experiment_dir,
                        executable_name=executable_name,
                        geos_directory=geos,
                        geos_install_path=geos_install_path,
                    )

                    # Run 1 timestep for cache build
                    slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_GPU)
                    slurm_config.output = "benchmark.cache.dacegpu.%t.out"
                    srun_script = _make_srun_script(
                        executable_name=executable_name,
                        experiment_directory=experiment_dir,
                        slurm_config=slurm_config,
                        gtfv3_config=GTFV3_DaCeGPU_Orchestrated_32bit,
                        prolog_scripts=prolog_scripts,
                    )
                    ShellScript(
                        name="setup_config_1ts_1node_gtfv3",
                        working_directory=experiment_dir,
                    ).write(
                        shell_commands=[
                            f"cd {experiment_dir}",
                            "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                            "cp -f input.nml.1x1 input.nml",
                            "cp -f CAP.rc.1ts CAP.rc",
                        ],
                    ).execute()
                    if not env.setup_only:
                        srun_script.execute()
                    else:
                        Progress.log(f"= = = Skipping {srun_script.name} = = =")

                # Run 1 day
                slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_GPU)
                slurm_config.output = "benchmark.1day.dacegpu.%t.out"
                gtfv3_config = dataclasses.replace(GTFV3_DaCeGPU_Orchestrated_32bit)
                gtfv3_config.FV3_DACEMODE = "Run"
                srun_script = _make_srun_script(
                    executable_name=executable_name,
                    experiment_directory=experiment_dir,
                    slurm_config=slurm_config,
                    gtfv3_config=gtfv3_config,
                    prolog_scripts=prolog_scripts,
                )
                ShellScript(
                    name="setup_config_1day_1node_gtfv3",
                    working_directory=experiment_dir,
                ).write(
                    shell_commands=[
                        f"cd {experiment_dir}",
                        "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                        "cp -f input.nml.1x1 input.nml",
                        "cp -f CAP.rc.1day CAP.rc",
                    ],
                ).execute()
                if not env.setup_only:
                    srun_script.execute()
                else:
                    Progress.log(f"= = = Skipping {srun_script.name} = = =")

                # Execute Fortran
                slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_CPU)
                slurm_config.output = "benchmark.1day.fortran.%t.out"
                srun_script = _make_srun_script(
                    executable_name=executable_name,
                    experiment_directory=experiment_dir,
                    slurm_config=SLURM_One_Half_Nodes_CPU,
                    gtfv3_config=gtfv3_config,
                    prolog_scripts=prolog_scripts,
                )
                ShellScript(
                    name="setup_config_1day_1node_gtfv3",
                    working_directory=experiment_dir,
                ).write(
                    shell_commands=[
                        f"cd {experiment_dir}",
                        "cp -f AgcmSimple.rc.3x24.fortran AgcmSimple.rc",
                        "cp -f input.nml.3x4 input.nml",
                        "cp -f CAP.rc.1day CAP.rc",
                    ],
                ).execute()
                if not env.setup_only:
                    srun_script.execute()
                else:
                    Progress.log(f"= = = Skipping {srun_script.name} = = =")

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        # Setup
        geos_path = env.get("GEOS_BASE_DIRECTORY")
        geos_experiment_path = f"{geos_path}/../experiment"
        artifact_directory = f"{env.artifact_directory}/held_suarez/"
        os.mkdir(artifact_directory)

        # Metadata
        file_exists = os.path.isfile("ci_metadata")
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata. Coding or Permission error."
            )
        shutil.copy("ci_metadata", artifact_directory)

        # Logs
        if (
            env.experiment_action == PipelineAction.Validation
            or env.experiment_action == PipelineAction.All
        ):
            logs = glob.glob(
                f"{geos_experiment_path}/{VALIDATION_RESOLUTION}/validation.*"
            )
            for log in logs:
                shutil.copy(log, artifact_directory)

        if (
            env.experiment_action == PipelineAction.Benchmark
            or env.experiment_action == PipelineAction.All
        ):
            for resolution in ["C180-L72", "C180-L91", "C180-L137"]:
                logs = glob.glob(f"{geos_experiment_path}/{resolution}/benchmark.*")
                for log in logs:
                    shutil.copy(log, artifact_directory)

        return True
