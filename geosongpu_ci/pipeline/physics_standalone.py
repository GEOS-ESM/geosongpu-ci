from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any, Optional
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.git import git_prelude
from geosongpu_ci.actions.discover import one_gpu_srun
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
    compiler: str = "nvfortran",
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

    if compiler == "gfortran":
        cpu_flags = "-g -O3 -fPIC -ffree-line-length-0"
    elif compiler == "nvfortran":
        cpu_flags = "-O3 -Mflushz -Mfunc32 -Kieee"
    else:
        raise RuntimeError(f"Compiler {compiler} not implemented.")

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
            f'FFLAGS="{cpu_flags}" {one_gpu_srun("build.out")} make',
            "cp TEST_MOIST TEST_MOIST_SERIAL",
            "make clean",
            f"{one_gpu_srun('build.out')} make",
            "cp TEST_MOIST TEST_MOIST_OACC",
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
        exe_cmd = one_gpu_srun(f"out.serial.{physics_name}.{i}.log")
        exe_cmd += (
            f" ./{physics_name}/TEST_MOIST_SERIAL ./c180_data/{input_data_name} {i}\n"
        )
        exe_cmd += one_gpu_srun(f"out.oacc.{physics_name}.{i}.log")
        exe_cmd += (
            f" ./{physics_name}/TEST_MOIST_OACC ./c180_data/{input_data_name} {i}\n"
        )
        scripts.append(exe_cmd)

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
    def _parse_log(filepath: str) -> Dict[Any, Any]:
        # Expected format
        #  #CI#VAR|xxxx#KEY|yyyy
        # with xxxx the varname
        # and the KEY / yyyy a key, value data to check
        # with KEY = [NEW, DIFF, REF]
        results = {}
        with open(filepath) as f:
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
        return results

    for i in range(0, 5):
        oacc_log_name = f"out.oacc.{physics_name}.{i}.log"
        serial_log_name = f"out.serial.{physics_name}.{i}.log"
        file_exists = os.path.isfile(oacc_log_name) and os.path.isfile(serial_log_name)
        if not file_exists:
            raise CICheckException(
                "Physics standalone: ",
                f"{oacc_log_name} or {serial_log_name} doesn't exists.",
            )

        oacc_results = _parse_log(oacc_log_name)
        serial_results = _parse_log(serial_log_name)

        print("Physics standalone checks variable against a 0.01% of the reference.")
        print("Raw results for OACC (pre-check):")
        print(oacc_results)

        threshold_tenth_of_a_percent = 0.01 / 100
        for varname in serial_results.keys():
            serial_value = serial_results[varname]["NEW"]
            oacc_value = oacc_results[varname]["NEW"]
            threshold = abs(threshold_tenth_of_a_percent * serial_value)
            diff = abs(oacc_value - serial_value)
            if diff > threshold:
                raise CICheckException(
                    f"Physics standalone variable {varname} fails:\n"
                    f"-      serial: {serial_value}\n"
                    f"-        oacc: {oacc_value}\n"
                    f"-   threshold: {threshold}\n"
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
            compiler="gfortran",
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
