from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.slurm import SlurmConfiguration
from geosongpu_ci.utils.shell import shell_script, execute_shell_script
from typing import Dict, Any, Optional
import shutil
import os
import dataclasses
import glob


@dataclasses.dataclass
class GTFV3Config:
    FV3_DACEMODE: str = "BuildAndRun"
    PACE_CONSTANTS: str = "GEOS"
    PACE_FLOAT_PRECISION: int = 32
    PACE_LOGLEVEL: str = "DEBUG"
    GTFV3_BACKEND: str = "dace:gpu"

    def bash(self) -> str:
        return (
            f"export FV3_DACEMODE={self.FV3_DACEMODE}\n"
            f"export PACE_CONSTANTS={self.PACE_CONSTANTS}\n"
            f"export PACE_FLOAT_PRECISION={self.PACE_FLOAT_PRECISION}\n"
            f"export PACE_LOGLEVEL={self.PACE_LOGLEVEL}\n"
            f"export GTFV3_BACKEND={self.GTFV3_BACKEND}\n"
        )


def _copy_input_from_project(
    input_directory: str,
    geos_directory: str,
    resolution: str,
    experiment_name: Optional[str] = None,
) -> str:
    if experiment_name:
        experiment_dir = f"{geos_directory}/experiment/{experiment_name}"
    else:
        experiment_dir = f"{geos_directory}/experiment/{resolution}"
    shell_script(
        name="copy_input",
        modules=[],
        shell_commands=[
            f"cd {geos_directory}",
            f"mkdir -p {experiment_dir}",
            f"cd {experiment_dir}",
            f"cp -r {input_directory}/* .",
        ],
    )
    return experiment_dir


def _make_gpu_wrapper_script(experiment_dir: str):
    shell_script(
        name=f"{experiment_dir}/gpu-wrapper-slurm",
        modules=[],
        shell_commands=[
            "#!/usr/bin/env sh",
            "export CUDA_VISIBLE_DEVICES=$SLURM_LOCALID",
            'echo "Node: $SLURM_NODEID | Rank: $SLURM_PROCID,'
            ' pinned to GPU: $CUDA_VISIBLE_DEVICES"',
            "$*",
        ],
        make_executable=True,
        execute=False,
    )


def _set_python_environment(geos_install_dir: str, executable_name: str, geos_dir: str):
    geos_fvdycore_comp = (
        f"{geos_install_dir}/../src/Components/@GEOSgcm_GridComp/"
        "GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp"
    )
    shell_script(
        name="setenv",
        shell_commands=[
            f'echo "Copy execurable {executable_name}"',
            "",
            f"cp {geos_install_dir}/bin/{executable_name} {geos_dir}/experiment/l1x1",
            "",
            'echo "Loading env (g5modules & pyenv)"',
            f"source {geos_install_dir}/../@env/g5_modules.sh",
            f'VENV_DIR="{geos_fvdycore_comp}/geos-gtfv3/driver/setenv/gtfv3_venv"',
            f'GTFV3_DIR="{geos_fvdycore_comp}/@gtFV3"',
            f'GEOS_INSTALL_DIR="{geos_install_dir}"',
            f"source {geos_fvdycore_comp}/geos-gtfv3/driver/setenv/pyenv.sh",
        ],
        execute=False,
    )


def _make_srun_script(
    executable_name: str,
    experiment_directory: str,
    slurm_config: SlurmConfiguration,
    gtfv3_config: GTFV3Config,
) -> str:
    srun_script_name = shell_script(
        name="srun_script",
        env_to_source=[
            "./setenv.sh",
        ],
        shell_commands=[
            f"cd {experiment_directory}",
            "",
            f"{gtfv3_config.bash()}",
            "export PYTHONOPTIMIZE=1",
            f"export CUPY_CACHE_DIR={experiment_directory}/.cupy",
            "",
            f"{slurm_config.srun_bash('./gpu-wrapper-slurm.sh', executable_name)}",
        ],
        execute=False,
    )
    return srun_script_name


def _setup_env_scripts(
    experiment_dir: str,
    executable_name: str,
    geos_install_path: str,
    geos_directory: str,
):
    _make_gpu_wrapper_script(experiment_dir)

    _set_python_environment(geos_install_path, executable_name, geos_directory)


def _setup_experiment(
    config: Dict[str, Any],
    geos_directory: str,
    geos_install_path: str,
    executable_name: str,
    resolution: str,
    experiment_name: Optional[str] = None,
):
    experiment_dir = _copy_input_from_project(
        input_directory=config["input"][resolution],
        geos_dir=geos_directory,
        resolution=resolution,
        experiment_name=experiment_name,
    )

    srun_script = _make_srun_script(
        executable_name=executable_name,
        experiment_directory=experiment_dir,
        slurm_config=SlurmConfiguration(),
        gtfv3_config=GTFV3Config(),
    )

    return srun_script, experiment_dir


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


@Registry.register
class HeldSuarez(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Setup
        geos_install_path = env.get("GEOS_INSTALL")
        geos = f"{geos_install_path}/.."
        executable_name = "./GEOShs.x"

        # # # Validation # # #
        if action == PipelineAction.Validation or action == PipelineAction.All:
            # Validation on C180-L72 data
            # Get experiment directory ready
            resolution = "C180-L72"
            experiment_dir = _copy_input_from_project(
                input_directory=config["input"][resolution],
                geos_directory=geos,
                resolution=resolution,
            )
            _setup_env_scripts(
                experiment_dir=experiment_dir,
                executable_name=executable_name,
                geos_install_path=geos_install_path,
                geos_directory=geos,
            )

            # Run 1 timestep for cache build
            slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_GPU)
            slurm_config.output = "validation.cache.dacegpu.%t.out"
            srun_script = _make_srun_script(
                executable_name=executable_name,
                experiment_directory=experiment_dir,
                slurm_config=slurm_config,
                gtfv3_config=GTFV3_DaCeGPU_Orchestrated_32bit,
            )
            shell_script(
                name="setup_config_1ts_1node_gtfv3",
                shell_commands=[
                    f"cd {experiment_dir}",
                    "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                    "cp -f input.nml.1x1 input.nml",
                    "cp -f CAP.rc.1ts CAP.rc",
                ],
            )
            execute_shell_script(srun_script)

            # TODO: more to be done to actually check on the results rather then
            # just "can run".

        # # # Benchmark # # #
        if action == PipelineAction.Benchmark or action == PipelineAction.All:
            # We run a range of resolution. C180-L72 might already be ran
            for resolution in ["C180-L72", "C180-L91", "C180-L137"]:
                if resolution == "C180-L72" and action == PipelineAction.All:
                    # In case validation ran already, we have the experiment dir
                    # and the cache ready to run
                    experiment_dir = f"{geos}/experiment/{resolution}"
                    pass
                else:
                    # Get experiment directory ready
                    experiment_dir = _copy_input_from_project(
                        input_directory=config["input"][resolution],
                        geos_directory=geos,
                        resolution=resolution,
                    )
                    _setup_env_scripts(
                        experiment_dir=experiment_dir,
                        executable_name=executable_name,
                        geos_install_path=geos_install_path,
                        geos_directory=geos,
                    )

                    # Run 1 timestep for cache build
                    slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_GPU)
                    slurm_config.output = "benchmark.cache.dacegpu.%t.out"
                    srun_script = _make_srun_script(
                        executable_name=executable_name,
                        experiment_directory=experiment_dir,
                        slurm_config=slurm_config,
                        gtfv3_config=GTFV3_DaCeGPU_Orchestrated_32bit,
                    )
                    shell_script(
                        name="setup_config_1ts_1node_gtfv3",
                        shell_commands=[
                            f"cd {experiment_dir}",
                            "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                            "cp -f input.nml.1x1 input.nml",
                            "cp -f CAP.rc.1ts CAP.rc",
                        ],
                    )
                    execute_shell_script(srun_script)

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
                )
                shell_script(
                    name="setup_config_1day_1node_gtfv3",
                    shell_commands=[
                        f"cd {experiment_dir}",
                        "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                        "cp -f input.nml.1x1 input.nml",
                        "cp -f CAP.rc.1day CAP.rc",
                    ],
                )
                execute_shell_script(srun_script)

                # Execute Fortran
                slurm_config = dataclasses.replace(SLURM_One_Half_Nodes_CPU)
                slurm_config.output = "benchmark.1day.fortran.%t.out"
                srun_script = _make_srun_script(
                    executable_name=executable_name,
                    experiment_directory=experiment_dir,
                    slurm_config=SLURM_One_Half_Nodes_CPU,
                )
                shell_script(
                    name="setup_config_1day_1node_gtfv3",
                    shell_commands=[
                        f"cd {experiment_dir}",
                        "cp -f AgcmSimple.rc.3x24.fortran AgcmSimple.rc",
                        "cp -f input.nml.3x4 input.nml",
                        "cp -f CAP.rc.1day CAP.rc",
                    ],
                )
                execute_shell_script(srun_script)

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_base_directory: str,
        env: Environment,
    ) -> bool:
        # Setup
        geos_install_path = env.get("GEOS_INSTALL")
        geos_experiment_path = f"{geos_install_path}/../experiment"
        artifact_directory = f"{artifact_base_directory}/held_suarez/"
        os.mkdir(artifact_directory)

        # Metadata
        file_exists = os.path.isfile("ci_metadata")
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata. Coding or Permission error."
            )
        shutil.copy("ci_metadata", artifact_directory)

        # Logs
        if action == PipelineAction.Validation or action == PipelineAction.All:
            logs = glob.glob(f"{geos_experiment_path}/C180-L72/validation.*")
            for log in logs:
                shutil.copy(log, artifact_directory)

        if action == PipelineAction.Benchmark or action == PipelineAction.All:
            for resolution in ["C180-L72", "C180-L91", "C180-L137"]:
                logs = glob.glob(f"{geos_experiment_path}/{resolution}/validation.*")
                for log in logs:
                    shutil.copy(log, artifact_directory)

        return True
