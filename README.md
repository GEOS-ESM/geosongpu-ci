
# GEOS on GPU - Continuous Integration

On-premise CI for the GPU ports of GEOS. Includes validation & benchmark worfklows.

## Validation status

Heartbeat insure the workflow to reach Discover is working.
Validation capacities in the case of GEOS is stricly building & running the GPU-enabled version.
Validation capacities for physics compares OACC and original Fortran on.

| Validation                    | Status    |
| ------------------------------------------ | --------- |
| NCCS Discover Heartbeat                    | [![💓](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_heartbeat_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_heartbeat_nightly.yml) |
| NCCS Discover GEOS Held-Suarez Validation  | [![HS](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_hs_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_hs_nightly.yml) |
| NCCS Discover Physics Standalone           | Deactivated |
| NCCS Discover GEOS Aquaplanet Validation   | [![AQ](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_aq_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_aq_nightly.yml) |

## Benchmarking capacities

Automatic benchmarking are as follow (legends after table)

| Experimentation               | Resolutions | Layout | CPU/GPU                           |
| ----------------------------- | ----------- | ------ | --------------------------------- |
| Held-Suarez                   | C180-L72    | 4x4    | 96/8 Node-to-node (sharing GPU)   |
|                               | C180-L137   | 4x4    | 96/8 Node-to-node (sharing GPU)   |
|                               | C360-L72    | 4x4    | 96/8 Node-to-node (sharing GPU)   |
| Aquaplanet                    | C180-L72    | 1x1    | 6/6  Node-to-node (exclusive GPU) |

Legend:

* Resolutions:
  * CXX: resolution of a cube-sphere face
  * LXX: number of atmospheric levels
* Setup:
  * Node-to-node (exclusive GPU): as per machine configuration, using exactly 1 GPU for one cube-sphere and the machine equivalent CPU socket.
    * On Discover:
      * GPU: 1 A100 and 1 EPYC 7402 core
      * CPU: 12 EPYC 7402 core
  * Node-to-node (sharing GPU): as per machine configuration, sharing 1 GPU for the machine equivalent CPU socket worth of ranks.
    * On Discover (using Nvidia's MPS):
      * GPU: 1 A100 and 12 EPYC 7402 core
      * CPU: 12 EPYC 7402 core

## Structure

Experiments are listed in `experiments/experiments.yaml`

The package install a `geosongpu_dispatch`

```text
Usage: geosongpu_dispatch [OPTIONS] NAME ACTION

  Dispatch the _NAME_ experiment (as recorded in experiments.yaml) with the
  _ACTION_ (from  Validation, Benchmark or All).

  Environement variable:

      CI_WORKSPACE: dispatch sets all work in this directory.

Options:
  --artifact TEXT  Artifact directory for results storage
  --setup_only     Setup the experiment but skip any long running jobs (build,
                   run...)
  --help           Show this message and exit.
```

The workflows are either automated (nightly, weekly) or on-demand via the Actions tab.

Another way of triggering workflow is to use the `/bot` command within PR comments.
You can look at the options by commenting `/bot help` on a PR and the bot will respond:

```text
Bot commands:

/bot help
: Print this message

/bot experience --name=[per experiment.yaml] --action=[All, Validation, Benchmark]
: Triggers a geosongpu_dispatch command with given parameters
```

## Documentation

Build with pdoc with

```python
pdoc -o ./docs geosongpu_ci
```

Documentation is available on [Github Pages](https://geos-esm.github.io/geosongpu-ci/geosongpu_ci.html) and will be build automatically at every `main` commit
