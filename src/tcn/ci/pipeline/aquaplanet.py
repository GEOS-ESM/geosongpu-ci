import glob
import os
import shutil
from typing import Any, Dict

import click

from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.pipeline.geos import copy_input_to_experiment_directory
from tcn.ci.pipeline.task import TaskBase, get_config
from tcn.benchmark.geos_log_parser import parse_geos_log
from tcn.benchmark.report import report
from tcn.ci.utils.environment import Environment
from tcn.ci.utils.progress import Progress
from tcn.ci.utils.registry import Registry
from tcn.ci.utils.shell import ShellScript


def _replace_in_file(url: str, text_to_replace: str, new_text: str):
    data = None
    with open(url, "r") as f:
        data = f.read()
        data = data.replace(text_to_replace, new_text)
    with open(url, "w") as f:
        f.write(data)


VALIDATION_RESOLUTION = "C180-L72"


@Registry.register
class Aquaplanet(TaskBase):
    def prepare_experiment(
        self,
        input_directory: str,
        geos_directory: str,
    ) -> str:
        experiment_directory = copy_input_to_experiment_directory(
            input_directory=input_directory,
            geos_directory=geos_directory,
            resolution=VALIDATION_RESOLUTION,
        )

        # Modify all gcm_run.j.X with directory information
        gcm_runs = glob.glob(f"{experiment_directory}/gcm_run.j.*")
        for gcm_run in gcm_runs:
            _replace_in_file(
                url=gcm_run,
                text_to_replace="setenv GEOSBASE TO_BE_REPLACED",
                new_text=f"setenv GEOSBASE {geos_directory}",
            )
            _replace_in_file(
                url=gcm_run,
                text_to_replace="setenv EXPDIR TO_BE_REPLACED",
                new_text=f"setenv EXPDIR {experiment_directory}",
            )

        return experiment_directory

    def simulate(
        self,
        experiment_directory: str,
        setup_sh: str,
        cap_rc: str,
        log_pattern: str,
        fv3_dacemode: str,
        setup_only: bool = False,
    ):
        executor_name = f"{setup_sh.replace('sh', '')}_{cap_rc}.sbatch"
        executor_name.replace("/", "-")  # sanitize
        if not setup_only:
            ShellScript("temporary_setup").write(
                shell_commands=[
                    f"cd {experiment_directory}",
                    f"./{setup_sh}",
                    f"cp -f {cap_rc} CAP.rc",
                ]
            ).execute(remove_after_execution=True)
            _replace_in_file(
                url=f"{experiment_directory}/gcm_run.j",
                text_to_replace="#SBATCH --output=slurm-%j-%x.out",
                new_text=f"#SBATCH --output={log_pattern}",
            )
            _replace_in_file(
                url=f"{experiment_directory}/gcm_run.j",
                text_to_replace="setenv FV3_DACEMODE BuildAndRun",
                new_text=f"setenv FV3_DACEMODE {fv3_dacemode}",
            )
            ShellScript(executor_name).write(
                shell_commands=[
                    f"cd {experiment_directory}",
                    f"export CUPY_CACHE_DIR={experiment_directory}/.cupy",
                    "sbatch gcm_run.j",
                ]
            ).execute(sbatch=True)
        else:
            Progress.log(f"= = = Skipping {executor_name} = = =")

    def run_action(
        self,
        config: Dict[str, Any],
        env: Environment,
        metadata: Dict[str, Any],
    ):
        geos = env.get("GEOS_BASE_DIRECTORY")
        validation_experiment_dir = None
        resolution = None

        if (
            env.experiment_action == PipelineAction.All
            or env.experiment_action == PipelineAction.Validation
        ):
            # Prepare experiment directory
            resolution = VALIDATION_RESOLUTION
            experiment_dir = self.prepare_experiment(
                input_directory=config["input"][VALIDATION_RESOLUTION],
                geos_directory=geos,
            )
            validation_experiment_dir = experiment_dir

            # Execute caching step on 6 GPUs
            self.simulate(
                experiment_directory=experiment_dir,
                setup_sh="setup_1.5nodes_gpu.sh",
                cap_rc="CAP.rc.1ts",
                log_pattern="validation.cache.dacegpu.%t.out",
                fv3_dacemode="BuildAndRun",
            )

            # Run for 12h on 6 GPUs
            self.simulate(
                experiment_directory=experiment_dir,
                setup_sh="setup_1.5nodes_gpu.sh",
                cap_rc="CAP.rc.12hours",
                log_pattern="validation.12hours.dacegpu.%t.out",
                fv3_dacemode="Run",
            )

        if (
            env.experiment_action == PipelineAction.All
            or env.experiment_action == PipelineAction.Benchmark
        ):
            if (
                resolution == VALIDATION_RESOLUTION
                and env.experiment_action == PipelineAction.All
            ):
                # Experiment directory is already present and backend cached
                experiment_dir = validation_experiment_dir
            else:
                # Build experiment directory & run cache
                experiment_dir = self.prepare_experiment(
                    input_directory=config["input"][VALIDATION_RESOLUTION],
                    geos_directory=geos,
                )
                self.simulate(
                    experiment_directory=experiment_dir,
                    setup_sh="setup_1.5nodes_gpu.sh",
                    cap_rc="CAP.rc.1ts",
                    log_pattern="benchmark.cache.dacegpu.%t.out",
                    fv3_dacemode="BuildAndRun",
                )

            # Execute 1 day run on 6 GPUs
            self.simulate(
                experiment_directory=experiment_dir,  # type: ignore
                setup_sh="setup_1.5nodes_gpu.sh",
                cap_rc="CAP.rc.1day",
                log_pattern="benchmark.1day.dacegpu.%t.out",
                fv3_dacemode="Run",
            )

            # Execute 1 day run on 72 CPUs (fortran)
            self.simulate(
                experiment_directory=experiment_dir,  # type: ignore
                setup_sh="setup_1.5nodes_cpu.sh",
                cap_rc="CAP.rc.1day",
                log_pattern="benchmark.1day.fortran.%t.out",
                fv3_dacemode="Run",
            )

    def check(
        self,
        config: Dict[str, Any],
        env: Environment,
    ) -> bool:
        # Setup
        geos_path = env.get("GEOS_BASE_DIRECTORY")
        geos_experiment_path = f"{geos_path}/experiment"
        artifact_directory = f"{env.artifact_directory}/Aquaplanet/"
        os.makedirs(artifact_directory, exist_ok=True)

        # Metadata
        ci_metadata_rpath = f"{geos_path}/../ci_metadata"
        file_exists = os.path.isfile(ci_metadata_rpath)
        if not file_exists:
            raise RuntimeError(
                "Held-Suarez run didn't write ci_metadata at "
                f"{ci_metadata_rpath}. "
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
            for resolution in ["C180-L72"]:
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
        "Running Aquaplanet:\n"
        f"        step: {step}\n"
        f"      action: {action}\n"
        f"    artifact: {artifact}\n"
        f"  setup only: {setup_only}"
    )

    # Rebuild the basics
    experience_name = "geos_aq"
    task = Registry.registry["Aquaplanet"]()
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
        RuntimeError(f"Coding error. Step {step} unknown on AQ cli")


if __name__ == "__main__":
    cli()
