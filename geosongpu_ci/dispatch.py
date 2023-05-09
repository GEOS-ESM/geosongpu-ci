from geosongpu_ci.pipeline.task import dispatch
from geosongpu_ci.actions.pipeline import PipelineAction


def main():
    """
    Expected:
        arg[1]: experiment name as listed in the experiments.yaml
        arg[2]: experiment action from PipelineAction
        arg[3]: artifact directory for LT storage
    """
    import sys

    experiment_name = sys.argv[1]
    experiment_action = PipelineAction[sys.argv[2]]
    artifact_directory = sys.argv[3]
    dispatch(experiment_name, experiment_action, artifact_directory)
