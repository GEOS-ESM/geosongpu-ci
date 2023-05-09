from geosongpu_ci.utils.environment import Environment
from typing import Dict, Any
from geosongpu_ci.pipeline.task import TaskBase
from geosongpu_ci.utils.shell import shell_script
from geosongpu_ci.utils.registry import Registry
from geosongpu_ci.actions.pipeline import PipelineAction
from geosongpu_ci.actions.git import git_prelude
from geosongpu_ci.utils.ci_exception import CICheckException
import os


@Registry.register
class OACCMoistRadCoup(TaskBase):
    def run_action(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        env: Environment,
        metadata: Dict[str, Any],
    ):
        repo_name = "moist_radcoup_loop"

        git_prelude(
            config,
            experiment_name,
            action,
            metadata,
            override_repo_name=repo_name,
            do_mepo=False,
        )

        # Build
        shell_script(
            name="build",
            modules=["comp/nvhpc/22.3"],
            env_to_source=[],
            shell_commands=[
                f"cd {repo_name}",
                f"export TMP={env.CI_WORKSPACE}/tmp",
                "export TMPDIR=$TMP",
                "export TEMP=$TMP",
                "mkdir $TMP",
                "make",
            ],
        )

        # Prepare input
        shell_script(
            name="prepare_input",
            modules=[],
            env_to_source=[],
            shell_commands=[
                "ln -s /discover/nobackup/projects/geosongpu/physics_standalone_data/moist/c180_data c180_data",
            ],
        )

        scripts = []
        for i in range(0, 5):
            scripts.append(
                f"srun --partition=gpu_a100 --constraint=rome --mem-per-gpu=40G --gres=gpu:1 --time=00:10:00 ./{repo_name}/TEST_MOIST ./c24_data/radcoup_loop {i} >| oacc_out.{i}.log"
            )

        # Run and store in oacc_run.log for mining later
        shell_script(
            name="srun_oacc",
            modules=[],
            env_to_source=[],
            shell_commands=scripts,
        )

    def check(
        self,
        config: Dict[str, Any],
        experiment_name: str,
        action: PipelineAction,
        artifact_directory: str,
        env: Environment,
    ) -> bool:
        for i in range(0, 5):
            log_name = f"oacc_out.{i}.log"
            file_exists = os.path.isfile(log_name)
            if not file_exists:
                raise CICheckException(
                    f"Physics standalone: {log_name} doesn't exists."
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
                    next_offset = log_as_str[read_head + 1 :].find(pattern)
                    if next_offset < 0:
                        break
                    read_head += next_offset + 1
                    infinite_loop_threshold -= 1
                if infinite_loop_threshold < 0:
                    raise RuntimeError(
                        "Log analysis ran for more than 10000 iterations - unlikely...."
                    )
                print(results)

            # Check results are below a fixed theshold
            error_threshold = 1e-5
            for var, value in results:
                if value > error_threshold:
                    raise CICheckException(
                        f"Physics standalone: variable {var} fails (diff is {error_threshold})"
                    )
