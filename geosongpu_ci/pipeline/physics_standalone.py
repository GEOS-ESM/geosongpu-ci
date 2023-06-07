from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any, Optional
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.git import git_prelude
from geosongpu_ci.utils.ci_exception import CICheckException
import os


def _run_action(
    config: Dict[str, Any],
    experiment_name: str,
    action: PipelineAction,
    env: Environment,
    metadata: Dict[str, Any],
    physics_name: str,
    input_data_name: Optional[str] = None,
):
    if not input_data_name:
        input_data_name = physics_name

    git_prelude(
        config,
        experiment_name,
        action,
        metadata,
        override_repo_name=physics_name,
        do_mepo=False,
    )

    # Build
    shell_script(
        name="build",
        modules=["comp/nvhpc/22.3"],
        env_to_source=[],
        shell_commands=[
            f"cd {physics_name}",
            f"export TMP={env.CI_WORKSPACE}/tmp",
            "export TMPDIR=$TMP",
            "export TEMP=$TMP",
            "mkdir $TMP",
            "srun -A j1013 -C rome --qos=4n_a100 --partition=gpu_a100"
            " --mem-per-gpu=40G --gres=gpu:1 --time=00:10:00 make",
        ],
    )

    # Prepare input
    shell_script(
        name=f"prepare_input_{physics_name}",
        modules=[],
        env_to_source=[],
        shell_commands=[
            "mkdir c180_data",
            f"ln -s {config['input']['directory']} c180_data/{input_data_name}",
        ],
    )

    scripts = []
    for i in range(0, 5):
        scripts.append(
            "srun -A j1013 -C rome --qos=4n_a100 --partition=gpu_a100"
            f" --mem-per-gpu=40G --gres=gpu:1 --time=00:10:00 "
            f" ./{physics_name}/TEST_MOIST ./c180_data/{input_data_name} {i}"
            f" >| oacc_out.{physics_name}.{i}.log\n"
        )

    # Run and store in oacc_run.log for mining later
    shell_script(
        name=f"srun_{physics_name}",
        modules=[],
        env_to_source=[],
        shell_commands=scripts,
    )


def _check(
    config: Dict[str, Any],
    experiment_name: str,
    action: PipelineAction,
    artifact_directory: str,
    env: Environment,
    physics_name: str,
):
    for i in range(0, 5):
        log_name = f"oacc_out.{physics_name}.{i}.log"
        file_exists = os.path.isfile(log_name)
        if not file_exists:
            raise CICheckException(
                "Physics standalone: ",
                f"{log_name} doesn't exists.",
            )

        # Expected format
        #  #CI#VAR|xxxx#KEY|yyyy
        # with xxxx the varname
        # and the KEY / yyyy a key, value data to check
        # with KEY = [NEW, DIFF, REF]

        results = {}
        with open(log_name) as f:
            line = f.readline()
            while line != "":
                # Look for CI encoding prefix
                if line.strip().startswith("#CI"):
                    sections = line.strip()[4:].split("#")
                    # Var name
                    varname = sections[0].split("|")[1]
                    if varname not in results.keys():
                        results[varname] = {}
                    # Value
                    verb, value = sections[1].split("|")
                    results[varname][verb] = float(value)
                line = f.readline()

        print("Physics standalone checks variable against a 0.01% of the reference.")
        print("Raw results (pre-check):")
        print(results)

        threshold_tenth_of_a_percent = 0.01 / 100
        for varname, values in results.items():
            threshold = threshold_tenth_of_a_percent * values["REF"]
            if abs(values["DIFF"]) > threshold:
                raise CICheckException(
                    f"Physics standalone variable {varname} fails:\n"
                    f"-        diff: {values['DIFF']}\n"
                    f"-   threshold: {threshold}\n"
                    f"-         new: {values['NEW']}\n"
                    f"-   reference: {values['REF']}"
                )

    return True


@Registry.register
class OACCMoistRadCoup(TaskBase):
    name: str = "moist_radcoup_loop"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
            input_data_name="radcoup_loop",
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCGFDLMicrophysics(TaskBase):
    name: str = "gfdl_microphysics"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
            input_data_name="gfdl_cloud_microphys_driver",
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCBuoyancy(TaskBase):
    name: str = "buoyancy"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCCupGfSh(TaskBase):
    name: str = "cup_gf_sh"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCEvapSublPdfLoop(TaskBase):
    name: str = "evap_subl_pdf_loop"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCFillQ2Zero(TaskBase):
    name: str = "fill_q_2_zero"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
            input_data_name="fillq2zero",
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )


@Registry.register
class OACCAerActivation(TaskBase):
    name: str = "aer_activation"

    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        _run_action(
            config=config,
            experiment_name=experiment_name,
            action=action,
            env=env,
            metadata=metadata,
            physics_name=self.name,
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        return _check(
            config=config,
            experiment_name=experiment_name,
            action=action,
            artifact_directory=artifact_directory,
            env=env,
            physics_name=self.name,
        )
