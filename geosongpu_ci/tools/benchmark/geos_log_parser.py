from geosongpu_ci.tools.benchmark import BenchmarkRawData
from typing import Iterable, Optional
import re


_numeric_const_pattern = (
    "[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?"  # noqa
)
RE_NUMERIC = re.compile(_numeric_const_pattern, re.VERBOSE)


def _grep(
    filename: str,
    pattern: str,
    exclude_pattern: Optional[bool] = False,
    start_pattern: Optional[str] = None,
    end_pattern: Optional[str] = None,
) -> Iterable[str]:
    results = []
    check = start_pattern is None
    with open(filename, "r") as f:
        for line in f.readlines():
            if not check and start_pattern and start_pattern in line:
                check = True
            if end_pattern and end_pattern in line:
                break
            if pattern in line:
                if exclude_pattern and pattern in line:
                    line = "".join(line.split(pattern)[1:])
                if line != "":
                    results.append(line)
    return results


def _extract_numerics(strings: Iterable[str]) -> Iterable[float]:
    results = []
    for s in strings:
        for r in RE_NUMERIC.findall(s):
            results.append(r)

    return [float(r) for r in results]


def parse_geos_log(filename: str) -> BenchmarkRawData:
    benchmark = BenchmarkRawData()

    # Get backend
    is_gtfv3 = _grep(filename, "RUN_GTFV3:1", exclude_pattern=True) != []
    if not is_gtfv3:
        benchmark.backend = "fortran"
    else:
        backend_pattern = "backend: "
        benchmark.backend = (
            _grep(filename, backend_pattern, exclude_pattern=True)[0]
            .strip()
            .replace("\n", "")
        )

    # Get timings of FV
    if is_gtfv3:
        interface_timings = _grep(filename, "fv3_interf", exclude_pattern=True)
        benchmark.fv_dyncore_timings = _extract_numerics(interface_timings)

        dycore_timings = _grep(filename, "] Run...", exclude_pattern=True)
        benchmark.inner_dycore_timings = _extract_numerics(dycore_timings)
    else:
        dycore_timings = _grep(
            filename, "fv_dynamics: time taken", exclude_pattern=True
        )
        benchmark.fv_dyncore_timings = _extract_numerics(dycore_timings)

    # Get setup (grid, nodes)
    grid_stats = _grep(filename, "Resolution of dynamics restart")
    grid_stats = _extract_numerics(grid_stats)
    assert len(grid_stats) == 3
    benchmark.grid_resolution = (
        int(grid_stats[0]),
        int(grid_stats[1]),
        int(grid_stats[2]),
    )
    NX = _extract_numerics(
        _grep(filename, "Resource Parameter: NX:", exclude_pattern=True)
    )
    assert len(NX) == 1
    NX = int(NX[0])
    NY = _extract_numerics(
        _grep(filename, "Resource Parameter: NY:", exclude_pattern=True)
    )
    assert len(NY) == 1
    NY = int(NY[0])
    benchmark.node_setup = (NX, int(NY / 6), int(NX * (NY / 6) * 6))

    # Get details FV Grid Comp timings
    dyn_profiler_entry = "profiler: Times for component <DYN>"
    superdyn_profiler_exit = "profiler: Times for component <SUPERDYNAMICS>"
    dyn_profiler_patterns = [
        ("profiler: ------RUN", "RUN", ""),
        ("profiler: --------DYN_ANA", "DYN_ANA", "RUN"),
        ("profiler: --------DYN_PROLOGUE", "DYN_PROLOGUE", "RUN"),
        ("profiler: --------DYN_CORE", "DYN_CORE", "RUN"),
        ("profiler: ----------PROLOGUE", "PROLOGUE", "DYN_CORE"),
        ("profiler: ----------PULL_TRACERS", "PULL_TRACERS", "DYN_CORE"),
        ("profiler: ----------STATE_TO_FV", "STATE_TO_FV", "DYN_CORE"),
        ("profiler: ----------MAKE_NH", "MAKE_NH", "DYN_CORE"),
        ("profiler: ----------MASS_FIX", "MASS_FIX", "DYN_CORE"),
        ("profiler: ----------FV_DYNAMICS", "FV_DYNAMICS", "DYN_CORE"),
        ("profiler: ----------PUSH_TRACERS", "PUSH_TRACERS", "DYN_CORE"),
        ("profiler: ----------FV_TO_STATE", "FV_TO_STATE", "DYN_CORE"),
        ("profiler: --------DYN_EPILOGUE", "DYN_EPILOGUE", "RUN"),
        ("profiler: ------RUN2", "RUN2", ""),
    ]
    for pattern, shortname, parent in dyn_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_pattern=dyn_profiler_entry,
                end_pattern=superdyn_profiler_exit,
            )
        )
        benchmark.fv_gridcomp_detailed_profiling.append(
            (shortname, measures[4], parent)
        )

    # Model throughput
    gloabl_profiler_entry = "profiler: Model Throughput"
    global_run_time = _grep(
        filename, "profiler: --Run", start_pattern=gloabl_profiler_entry
    )
    benchmark.global_run_time = _extract_numerics(global_run_time)[1]

    return benchmark


if __name__ == "__main__":
    import sys

    log_parsed = parse_geos_log(sys.argv[1])
    print(log_parsed)
