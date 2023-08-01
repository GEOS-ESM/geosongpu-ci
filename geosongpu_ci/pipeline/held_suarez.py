import click
from geosongpu_ci.pipeline.task import TaskBase, get_config
from geosongpu_ci.utils.environment import Environment
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.slurm import SlurmConfiguration
from geosongpu_ci.utils.shell import ShellScript
from geosongpu_ci.pipeline.geos import (
    set_python_environment,
    copy_input_to_experiment_directory,
)
from geosongpu_ci.pipeline.gtfv3_config import GTFV3Config
from geosongpu_ci.utils.progress import Progress
from geosongpu_ci.tools.benchmark.geos_log_parser import parse_geos_log
from geosongpu_ci.tools.benchmark.report import report
from typing import Dict, Any
import shutil
import os
import dataclasses
import glob


class PrologScripts:
    """Scripts to setup and run an experiment

    Those are meant to be run and/or included in all runs"""

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


VALIDATION_RESOLUTION = "C180-L72"


@Registry.register
class HeldSuarez(TaskBase):
    """GEOS with Held-Suarez physics.

    Depends on the GEOS task to be run first.
    Proposes C180-LXX benchmarking and basic build worthiness validation.
    """

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
            experiment_dir = copy_input_to_experiment_directory(
                input_directory=config["input"][VALIDATION_RESOLUTION],
                geos_directory=geos,
                resolution=VALIDATION_RESOLUTION,
                trigger_reset=True,
            )
            prolog_scripts = PrologScripts(
                experiment_directory=experiment_dir,
                executable_name=executable_name,
                geos_directory=geos,
                geos_install_path=geos_install_path,
            )

            # Run 1 timestep for cache build
            slurm_config = SlurmConfiguration.one_half_nodes_GPU()
            slurm_config.output = "validation.cache.dacegpu.%t.out"
            srun_script = _make_srun_script(
                executable_name=executable_name,
                experiment_directory=experiment_dir,
                slurm_config=slurm_config,
                gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
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
                    experiment_dir = copy_input_to_experiment_directory(
                        input_directory=config["input"][resolution],
                        geos_directory=geos,
                        resolution=resolution,
                        trigger_reset=True,
                    )
                    prolog_scripts = PrologScripts(
                        experiment_directory=experiment_dir,
                        executable_name=executable_name,
                        geos_directory=geos,
                        geos_install_path=geos_install_path,
                    )

                    # Run 1 timestep for cache build
                    slurm_config = SlurmConfiguration.one_half_nodes_GPU()
                    slurm_config.output = "benchmark.cache.dacegpu.%t.out"
                    srun_script = _make_srun_script(
                        executable_name=executable_name,
                        experiment_directory=experiment_dir,
                        slurm_config=slurm_config,
                        gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
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
                slurm_config = SlurmConfiguration.one_half_nodes_GPU()
                slurm_config.output = "benchmark.1day.dacegpu.%t.out"
                gtfv3_config = dataclasses.replace(GTFV3Config.dace_gpu_32_bit_BAR())
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
                slurm_config = SlurmConfiguration.one_half_Nodes_CPU()
                slurm_config.output = "benchmark.1day.fortran.%t.out"
                srun_script = _make_srun_script(
                    executable_name=executable_name,
                    experiment_directory=experiment_dir,
                    slurm_config=slurm_config,
                    gtfv3_config=gtfv3_config,
                    prolog_scripts=prolog_scripts,
                )
                ShellScript(
                    name="setup_config_1day_1node_fortran",
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
        geos_experiment_path = f"{geos_path}/experiment"
        artifact_directory = f"{env.artifact_directory}/held_suarez/"
        os.makedirs(artifact_directory, exist_ok=True)

        # Metadata
        ci_metadata_rpath = f"{geos_path}/../ci_metadata"
        file_exists = os.path.isfile(ci_metadata_rpath)
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata at "
                f"{geos_experiment_path}/{VALIDATION_RESOLUTION}. "
                "Coding or Permission error."
            )
        shutil.copy(ci_metadata_rpath, artifact_directory)

        # Validation artefact save
        if (
            env.experiment_action == PipelineAction.Validation
            or env.experiment_action == PipelineAction.All
        ):
            logs = glob.glob(
                f"{geos_experiment_path}/{VALIDATION_RESOLUTION}/validation.*"
            )
            validation_artifact = f"{artifact_directory}/Validation/"
            os.makedirs(validation_artifact, exist_ok=True)
            for log in logs:
                shutil.copy(log, validation_artifact)

        # Benchmark artifact save & analysis
        if (
            env.experiment_action == PipelineAction.Benchmark
            or env.experiment_action == PipelineAction.All
        ):
            for resolution in ["C180-L72", "C180-L91", "C180-L137"]:
                logs = glob.glob(f"{geos_experiment_path}/{resolution}/benchmark.*")
                benchmark_artifact = f"{artifact_directory}/Benchmark/{resolution}"
                os.makedirs(benchmark_artifact, exist_ok=True)
                bench_raw_data = []
                for log in logs:
                    shutil.copy(log, benchmark_artifact)
                    # Grab all rank 0 that are not caching runs
                    if ".0.out" in log and "cache" not in log:
                        bench_raw_data.append(parse_geos_log(log))
                benchmark_report = report(bench_raw_data)
                print(benchmark_report)
                with open(f"{benchmark_artifact}/report_benchmark.out", "w") as f:
                    f.write(str(benchmark_report))

        return True


@click.command()
@click.argument("step")
@click.argument("geos_base_directory")
@click.option("--action", default="Validation")
@click.option("--artifact", default=".", help="Artifact directory for results storage")
@click.option(
    "--setup_only",
    is_flag=True,
    help="Setup the experiment but skip any long running jobs (build, run...)",
)
def cli(
    step: str, geos_base_directory: str, action: str, artifact: str, setup_only: bool
):
    # Validation step
    if step not in TaskBase.step_options():
        raise click.BadArgumentUsage(
            f"step needs to be from {TaskBase.step_options()} (given: {step})"
        )

    print(
        "Running HeldSuarez:\n"
        f"        step: {step}\n"
        f"      action: {action}\n"
        f"    artifact: {artifact}\n"
        f"  setup only: {setup_only}"
    )

    # Rebuild the basics
    experience_name = "geos_hs"
    task = Registry.registry["HeldSuarez"]()
    config = get_config(experience_name)
    env = Environment(
        experience_name=experience_name,
        experiment_action=PipelineAction[action],
        artifact_directory=artifact,
        setup_only=setup_only,
    )
    env.set("GEOS_BASE_DIRECTORY", geos_base_directory)

    if step == "all" or step == "run":
        task.run(config, env)
    elif step == "all" or step == "check":
        task.check(config, env)
    else:
        RuntimeError(f"Coding error. Step {step} unknown on HS cli")


if __name__ == "__main__":
    cli()
