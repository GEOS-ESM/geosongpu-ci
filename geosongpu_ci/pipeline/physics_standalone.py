from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any
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
):
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
            "make",
        ],
    )

    # Prepare input
    shell_script(
        name=f"prepare_input_{physics_name}",
        modules=[],
        env_to_source=[],
        shell_commands=[
            f"ln -s {config['input']['directory']} c180_data",
        ],
    )

    scripts = []
    for i in range(0, 5):
        scripts.append("srun --partition=gpu_a100 --constraint=rome \\")
        scripts.append(" --mem-per-gpu=40G --gres=gpu:1 \\")
        scripts.append(
            f" --time=00:10:00 ./{physics_name}/TEST_MOIST ./c180_data {i} \\"
        )
        scripts.append(f" >| oacc_out.{physics_name}.{i}.log")

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
        # Parse logs to acquire results
        with open(log_name) as f:
            log_as_str = f.read()
            pattern = "Compare sum(diff"
            read_head = log_as_str.find(pattern)
            results = {}
            infinite_loop_threshold = 10000
            while infinite_loop_threshold >= 0:
                # Search the next )
                read_head += len(pattern) + 1
                search_head = read_head + log_as_str[read_head:].find(")")
                assert search_head > read_head
                varname = log_as_str[read_head:search_head]
                read_head = search_head + 1
                # Look results
                read_head += log_as_str[read_head:].find("=") + 1
                search_head = read_head + log_as_str[read_head:].find("\n")
                number_as_str = log_as_str[read_head:search_head]
                value = float(number_as_str)
                # Store key/value
                results[varname] = value
                # Move to next line
                next_offset = log_as_str[(read_head + 1) :].find(pattern)
                if next_offset < 0:
                    break
                read_head += next_offset + 1
                infinite_loop_threshold -= 1
            if infinite_loop_threshold < 0:
                raise RuntimeError(
                    "Log analysis ran for more than 10000",
                    " iterations - unlikely....",
                )
            print(results)

        # Check results are below a fixed theshold
        error_threshold = 1e-3
        for var, value in results.items():
            if abs(value) > error_threshold:
                raise CICheckException(
                    f"Physics standalone: variable {var}",
                    f" fails (diff is {value})",
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
    name: str = "oacc_buoyancy"

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
    name: str = "oacc_cup_gf_sh"

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
    name: str = "oacc_evap_subl_pdf_loop"

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
    name: str = "oacc_fill_q_2_zero"

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
