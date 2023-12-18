import click
from tcn.ci.pipeline.task import TaskBase, get_config
from tcn.utils.environment import Environment
from tcn.utils.registry import Registry
from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.actions.slurm import SlurmConfiguration
from tcn.utils.shell import ShellScript
from tcn.ci.pipeline.geos import (
    set_python_environment,
    copy_input_to_experiment_directory,
)
from tcn.ci.pipeline.gtfv3_config import GTFV3Config
from tcn.utils.progress import Progress
from tcn.tools.benchmark.geos_log_parser import parse_geos_log
from tcn.tools.benchmark.report import report
from typing import Dict, Any, Tuple
import shutil
import os
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

    def _make_gpu_wrapper_script(
        self,
        experiment_directory: str,
    ) -> None:
        self.gpu_wrapper = ShellScript(
            "gpu-wrapper-slurm-mps",
            working_directory=experiment_directory,
        ).from_template(template_name="gpu-wrapper-slurm-mps.sh")

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
    hardware_sampler_on: bool = False,
    mps_on: bool = False,
    local_redirect_log: bool = False,
) -> ShellScript:
    # Executing command with the SLURM setup
    srun_cmd = slurm_config.srun_bash(
        wrapper=prolog_scripts.gpu_wrapper.path,
        executable_name=executable_name,
    )
    # Options
    options = f"""{'export HARDWARE_SAMPLING=1' if hardware_sampler_on else 'unset HARDWARE_SAMPLING' }
{'export MPS_ON=1' if mps_on else 'unset MPS_ON' }
{f'export LOCAL_REDIRECT_LOG=1' if local_redirect_log else 'unset LOCAL_REDIRECT_LOG' }
    """

    if "dace" in gtfv3_config.GTFV3_BACKEND:
        backend = f"{gtfv3_config.backend_sanitized()}.{gtfv3_config.FV3_DACEMODE}"
    else:
        backend = f"{gtfv3_config.backend_sanitized()}"
    srun_script_name = f"srun_{slurm_config.ntasks}tasks_{backend}"

    srun_script = ShellScript(
        srun_script_name,
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
            f"export CUPY_CACHE_DIR={experiment_directory}/.cupy",
            "",
            f"{options}",
            "",
            f"{srun_cmd}",
        ],
    )
    return srun_script


VALIDATION_RESOLUTION = "C180-L72"


@Registry.register
class HeldSuarez(TaskBase):
    """GEOS with Held-Suarez physics.

    Depends on the GEOS task to be run first.
    Proposes C180-LXX benchmarking and basic build worthiness validation.
    """

    executable_name = "./GEOShs.x"

    def _setup_1ts_1node_gtfv3(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1ts_1node_gtfv3",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                "cp -f input.nml.1x1 input.nml",
                "cp -f CAP.rc.1ts CAP.rc",
            ],
        )

    def _setup_1day_1node_gtfv3(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1day_1node_gtfv3",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.1x6.gtfv3 AgcmSimple.rc",
                "cp -f input.nml.1x1 input.nml",
                "cp -f CAP.rc.1day CAP.rc",
            ],
        )

    def _setup_1day_1node_fortran(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1day_1node_fortran",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.3x24.fortran AgcmSimple.rc",
                "cp -f input.nml.3x4 input.nml",
                "cp -f CAP.rc.1day CAP.rc",
            ],
        )

    def _setup_1ts_2nodes_gtfv3(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1ts_2nodes_gtfv3",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.4x24.gtfv3 AgcmSimple.rc",
                "cp -f input.nml.4x4 input.nml",
                "cp -f CAP.rc.1ts CAP.rc",
            ],
        )

    def _setup_1day_2nodes_gtfv3(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1day_2nodes_gtfv3",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.4x24.gtfv3 AgcmSimple.rc",
                "cp -f input.nml.4x4 input.nml",
                "cp -f CAP.rc.1day CAP.rc",
            ],
        )

    def _setup_1day_2nodes_fortran(self, experiment_directory: str) -> ShellScript:
        return ShellScript(
            name="setup_config_1day_2nodes_fortran",
            working_directory=experiment_directory,
        ).write(
            shell_commands=[
                f"cd {experiment_directory}",
                "cp -f AgcmSimple.rc.4x24.fortran AgcmSimple.rc",
                "cp -f input.nml.4x4 input.nml",
                "cp -f CAP.rc.1day CAP.rc",
            ],
        )

    def prepare_experiment(
        self,
        input_directory: str,
        resolution: str,
        geos_directory: str,
        geos_install_directory: str,
        executable_name: str,
    ) -> Tuple[str, PrologScripts]:
        experiment_dir = copy_input_to_experiment_directory(
            input_directory=input_directory,
            geos_directory=geos_directory,
            resolution=resolution,
            trigger_reset=True,
        )
        prolog_scripts = PrologScripts(
            experiment_directory=experiment_dir,
            executable_name=executable_name,
            geos_directory=geos_directory,
            geos_install_path=geos_install_directory,
        )
        return experiment_dir, prolog_scripts

    def simulate(
        self,
        experiment_directory: str,
        executable_name: str,
        prolog_scripts: PrologScripts,
        slurm_config: SlurmConfiguration,
        gtfv3_config: GTFV3Config,
        setup_script: ShellScript,
        setup_only: bool = False,
        hardware_sampler_on: bool = False,
        mps_on: bool = False,
        local_redirect_log: bool = False,
    ):
        srun_script = _make_srun_script(
            executable_name=executable_name,
            experiment_directory=experiment_directory,
            slurm_config=slurm_config,
            gtfv3_config=gtfv3_config,
            prolog_scripts=prolog_scripts,
            hardware_sampler_on=hardware_sampler_on,
            mps_on=mps_on,
            local_redirect_log=local_redirect_log,
        )

        setup_script.execute()
        if not setup_only:
            srun_script.execute()
        else:
            Progress.log(f"= = = Skipping {srun_script.name} = = =")

    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        # Setup
        geos_install_directory = env.get("GEOS_INSTALL_DIRECTORY")
        geos = env.get("GEOS_BASE_DIRECTORY")
        validation_experiment_directory = None
        validation_prolog_script = None

        # # # Validation # # #
        if (
            env.experiment_action == PipelineAction.Validation
            or env.experiment_action == PipelineAction.All
        ):
            experiment_directory, prolog_scripts = self.prepare_experiment(
                input_directory=config["input"][VALIDATION_RESOLUTION],
                resolution=VALIDATION_RESOLUTION,
                geos_directory=geos,
                geos_install_directory=geos_install_directory,
                executable_name=self.executable_name,
            )

            # Run 1 timestep for cache build
            self.simulate(
                experiment_directory=experiment_directory,
                executable_name=self.executable_name,
                prolog_scripts=prolog_scripts,
                slurm_config=SlurmConfiguration.slurm_6CPUs_6GPUs(
                    output="validation.cache.dacegpu.%t.out"
                ),
                gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
                setup_script=self._setup_1ts_1node_gtfv3(experiment_directory),
                setup_only=env.setup_only,
            )

            # Cache for benchmark
            validation_experiment_directory = experiment_directory
            validation_prolog_script = prolog_scripts

        # # # Benchmark # # #
        if (
            env.experiment_action == PipelineAction.Benchmark
            or env.experiment_action == PipelineAction.All
        ):
            # We run a range of resolution. C180-L72 might already be ran
            for resolution in ["C180-L72", "C180-L137", "C360-L72"]:
                if (
                    resolution == VALIDATION_RESOLUTION
                    and env.experiment_action == PipelineAction.All
                ):
                    # In case validation ran already, we have the experiment dir
                    # and the cache ready to run
                    experiment_directory = validation_experiment_directory
                    prolog_scripts = validation_prolog_script
                else:
                    experiment_directory, prolog_scripts = self.prepare_experiment(
                        input_directory=config["input"][resolution],
                        resolution=resolution,
                        geos_directory=geos,
                        geos_install_directory=geos_install_directory,
                        executable_name=self.executable_name,
                    )

                    # Run 1 timestep for cache build
                    self.simulate(
                        experiment_directory=experiment_directory,
                        executable_name=self.executable_name,
                        prolog_scripts=prolog_scripts,
                        slurm_config=SlurmConfiguration.slurm_96CPUs_8GPUs(
                            output="benchmark.cache.dacegpu.%t.out"
                        ),
                        gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
                        setup_script=self._setup_1ts_2nodes_gtfv3(experiment_directory),
                        setup_only=env.setup_only,
                    )

                # Run 1 day gtfv3
                self.simulate(
                    experiment_directory=experiment_directory,  # type: ignore
                    executable_name=self.executable_name,
                    prolog_scripts=prolog_scripts,  # type: ignore
                    slurm_config=SlurmConfiguration.slurm_96CPUs_8GPUs(
                        output="benchmark.1day.MPS.44.dacegpu.%t.out"
                    ),
                    gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(dacemode="Run"),
                    setup_script=self._setup_1day_2nodes_gtfv3(experiment_directory),  # type: ignore
                    setup_only=env.setup_only,
                    mps_on=True,
                )

                # Run 1 day Fortran
                self.simulate(
                    experiment_directory=experiment_directory,  # type: ignore
                    executable_name=self.executable_name,
                    prolog_scripts=prolog_scripts,  # type: ignore
                    slurm_config=SlurmConfiguration.slurm_96CPUs(
                        output="benchmark.1day.MPS.44.fortran.%t.out"
                    ),
                    gtfv3_config=GTFV3Config.fortran(),
                    setup_script=self._setup_1day_2nodes_fortran(experiment_directory),  # type: ignore
                    setup_only=env.setup_only,
                    mps_on=True,
                )

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


@click.group()
@click.argument("geos_base_directory")
@click.pass_context
def cli(ctx, geos_base_directory):
    ctx.ensure_object(dict)
    ctx.obj["geos_base_directory"] = geos_base_directory


@cli.command()
@click.argument("step")
@click.option("--action", default="Validation")
@click.option("--artifact", default=".", help="Artifact directory for results storage")
@click.option(
    "--setup_only",
    is_flag=True,
    help="Setup the experiment but skip any long running jobs (build, run...)",
)
@click.pass_context
def pipe(ctx, step: str, action: str, artifact: str, setup_only: bool):
    geos_base_directory = ctx.obj["geos_base_directory"]

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


@cli.command()
@click.argument("resolution")
@click.option(
    "--setup_only",
    is_flag=True,
    help="Setup the experiment but skip any long running jobs (build, run...)",
)
@click.pass_context
def benchmark(
    ctx,
    resolution: str,
    setup_only: bool,
):
    geos_base_directory = ctx.obj["geos_base_directory"]
    geos_install_directory = f"{geos_base_directory}/install"

    # Rebuild the basics
    experience_name = "geos_hs"
    HS = HeldSuarez()
    config = get_config(experience_name)

    experiment_directory, prolog_scripts = HS.prepare_experiment(
        input_directory=config["input"][resolution],
        resolution=resolution,
        geos_directory=geos_base_directory,
        geos_install_directory=geos_install_directory,
        executable_name=HS.executable_name,
    )

    print(
        "Running HeldSuarez benchmark:\n"
        f"     resolution: {resolution}\n"
        f"     setup only: {setup_only}\n"
        f" experiment dir: {experiment_directory}"
    )

    # Run 1 timestep for cache build
    HS.simulate(
        experiment_directory=experiment_directory,
        executable_name=HS.executable_name,
        prolog_scripts=prolog_scripts,
        slurm_config=SlurmConfiguration.slurm_6CPUs_6GPUs(
            output="benchmark.cache.dacegpu.%t.out"
        ),
        gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
        setup_script=HS._setup_1ts_1node_gtfv3(experiment_directory),
        setup_only=setup_only,
    )
    HS.simulate(
        experiment_directory=experiment_directory,
        executable_name=HS.executable_name,
        prolog_scripts=prolog_scripts,
        slurm_config=SlurmConfiguration.slurm_6CPUs_6GPUs(
            output="benchmark.1day.dacegpu.%t.out"
        ),
        gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(dacemode="Run"),
        setup_script=HS._setup_1day_1node_gtfv3(experiment_directory),
        setup_only=setup_only,
    )
    HS.simulate(
        experiment_directory=experiment_directory,
        executable_name=HS.executable_name,
        prolog_scripts=prolog_scripts,
        slurm_config=SlurmConfiguration.slurm_72CPUs(
            output="benchmark.1day.fortran.%t.out"
        ),
        gtfv3_config=GTFV3Config.dace_gpu_32_bit_BAR(),
        setup_script=HS._setup_1day_1node_fortran(experiment_directory),
        setup_only=setup_only,
    )

    # Report
    bench_raw_data = []
    bench_raw_data.append(
        parse_geos_log(f"{experiment_directory}/benchmark.1day.dacegpu.0.out")
    )
    bench_raw_data.append(
        parse_geos_log(f"{experiment_directory}/benchmark.1day.fortran.0.out")
    )

    benchmark_report = report(bench_raw_data)
    print(benchmark_report)
    with open("report_benchmark.out", "w") as f:
        f.write(str(benchmark_report))


if __name__ == "__main__":
    cli()
