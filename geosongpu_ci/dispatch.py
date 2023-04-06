from geosongpu_ci.pipeline.task import dispatch
from geosongpu_ci.pipeline.actions import PipelineAction

if __name__ == "__main__":
    import sys

    experiment_name = sys.argv[1]
    experiment_action = PipelineAction[sys.argv[2]]
    dispatch(experiment_name, experiment_action)
