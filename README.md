# GEOS on GPU - Continuous Integration

| Test                    | Status    |
| ----------------------- | --------- |
| NCCS Discover Heartbeat                    | [![Discover Nightly Heartbeat](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_heartbeat_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_heartbeat_nightly.yml) |
| NCCS Discover GEOS Held-Suarez Validation  | [![Discover Nightly GEOS Held-Suarez Validation](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_hs_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_hs_nightly.yml) |
| NCCS Discover Physics Standalone           | [![Discover Nightly Physics Standalone Validation](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_physics_standalone_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_physics_standalone_nightly.yml) |
| NCCS Discover GEOS Aquaplanet Validation   | [![Discover Nightly GEOS Aquaplanet Validation](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_aq_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/geosongpu-ci/actions/workflows/discover_aq_nightly.yml) |

On-premise CI for the GPU ports of GEOS. Includes validation & benchmark worfklows.

## Current capacities

Experiments are listed in `experiments/experiments.yaml`

The package install a `geosongpu_dispatch`

```
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


## CI

The workflows are either automated (nightly, weekly) or on-demand via the Actions tab.

Another way of triggering workflow is to use the `/bot` command within PR comments.
You can look at the options by commenting `/bot help` on a PR and the bot will respond:

```
Bot commands:

/bot help
: Print this message

/bot experience --name=[per experiment.yaml] --action=[All, Validation, Benchmark]
: Triggers a geosongpu_dispatch command with given parameters
```