import click

from tcn.ci.actions.pipeline import PipelineAction
from tcn.ci.pipeline.task import dispatch


@click.command()
@click.argument("name")
@click.argument("action")
@click.option("--artifact", default=".", help="Artifact directory for results storage")
@click.option(
    "--setup_only",
    is_flag=True,
    help="Setup the experiment but skip any long running jobs (build, run...)",
)
def cli(name: str, action: str, artifact: str, setup_only: bool):
    """Dispatch the _NAME_ experiment (as recorded in experiments.yaml)
    with the _ACTION_ (from  Validation, Benchmark or All).

    Environement variable:\n
        CI_WORKSPACE: dispatch sets all work in this directory."""
    dispatch(name, PipelineAction[action], artifact, setup_only)


if __name__ == "__main__":
    cli()
