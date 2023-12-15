from smtn.tools.benchmark.raw_data import BenchmarkRawData
from typing import List, Optional
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
    expected: Optional[bool] = True,
) -> List[str]:
    results = []
    check = start_pattern is None
    with open(filename, "r") as f:
        for line in f.readlines():
            if not check and start_pattern and start_pattern in line:
                check = True
            if end_pattern and end_pattern in line:
                break
            if check and pattern in line:
                if exclude_pattern and pattern in line:
                    line = "".join(line.split(pattern)[1:])
                if line != "":
                    results.append(line)
    if expected and results == []:
        raise RuntimeError(f"Expecting {pattern} to be found")
    return results


def _extract_numerics(strings: List[str]) -> List[float]:
    results = []
    for s in strings:
        for r in RE_NUMERIC.findall(s):
            results.append(r)

    return [float(r) for r in results]


def parse_geos_log(filename: str) -> BenchmarkRawData:
    benchmark = BenchmarkRawData()

    # Get backend
    is_gtfv3 = (
        _grep(filename, "RUN_GTFV3:1", exclude_pattern=True, expected=False) != []
    )
    if not is_gtfv3:
        benchmark.backend = "fortran"
    else:
        backend_pattern = "backend : "
        grepped = _grep(filename, backend_pattern, exclude_pattern=True, expected=False)
        if grepped == []:
            benchmark.backend = "gtfv3 (details failed to parse)"
        else:
            backend = grepped[0].strip().replace("\n", "").replace(":", "")
            benchmark.backend = f"gtfv3_{backend}"

    # Get timings of FV
    if is_gtfv3:
        interface_timings = _grep(filename, " 0 , geos_gtfv3", exclude_pattern=True)
        benchmark.fv_dyncore_timings = _extract_numerics(interface_timings)

        if "dace" in benchmark.backend:
            dycore_timings = _grep(
                filename, "] Run...", exclude_pattern=True, expected=False
            )
            benchmark.inner_dycore_timings = _extract_numerics(dycore_timings)
    else:
        dycore_timings = _grep(filename, " 0: fv_dynamics", exclude_pattern=True)
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
    dyn_profiler_entry = "Times for component <DYN>"
    superdyn_profiler_exit = "Times for component <SUPERDYNAMICS>"
    dyn_profiler_patterns = [
        ("------RUN", "RUN", ""),
        ("--------DYN_ANA", "DYN_ANA", "RUN"),
        ("--------DYN_PROLOGUE", "DYN_PROLOGUE", "RUN"),
        ("--------DYN_CORE", "DYN_CORE", "RUN"),
        ("----------PROLOGUE", "PROLOGUE", "DYN_CORE"),
        ("----------PULL_TRACERS", "PULL_TRACERS", "DYN_CORE"),
        ("----------STATE_TO_FV", "STATE_TO_FV", "DYN_CORE"),
        ("----------MAKE_NH", "MAKE_NH", "DYN_CORE"),
        ("----------MASS_FIX", "MASS_FIX", "DYN_CORE"),
        ("----------FV_DYNAMICS", "FV_DYNAMICS", "DYN_CORE"),
        ("----------PUSH_TRACERS", "PUSH_TRACERS", "DYN_CORE"),
        ("----------FV_TO_STATE", "FV_TO_STATE", "DYN_CORE"),
        ("--------DYN_EPILOGUE", "DYN_EPILOGUE", "RUN"),
        ("------RUN2", "RUN2", ""),
    ]
    for pattern, shortname, parent in dyn_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_pattern=dyn_profiler_entry,
                end_pattern=superdyn_profiler_exit,
                expected=False,
            )
        )
        if measures != []:
            benchmark.fv_gridcomp_detailed_profiling.append(
                (shortname, measures[4], parent)
            )

    # Model throughput
    gloabl_profiler_entry = "Model Throughput"
    global_init_time = _grep(
        filename, "--Initialize", start_pattern=gloabl_profiler_entry
    )
    benchmark.global_init_time = _extract_numerics(global_init_time)[1]
    global_run_time = _grep(filename, "--Run", start_pattern=gloabl_profiler_entry)
    benchmark.global_run_time = _extract_numerics(global_run_time)[1]
    global_finalize_time = _grep(
        filename, "--Finalize", start_pattern=gloabl_profiler_entry
    )
    benchmark.global_finalize_time = _extract_numerics(global_finalize_time)[1]

    return benchmark


if __name__ == "__main__":
    import sys

    log_parsed = parse_geos_log(sys.argv[1])
    print(log_parsed)
