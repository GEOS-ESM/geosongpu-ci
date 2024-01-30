import re
from typing import List, Optional

from tcn.benchmark.raw_data import BenchmarkRawData

_numeric_const_pattern = (
    "[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?"  # noqa
)
RE_NUMERIC = re.compile(_numeric_const_pattern, re.VERBOSE)


def _grep(
    filename: str,
    pattern: str,
    exclude_pattern: Optional[bool] = False,
    start_patterns: Optional[List[str]] = None,
    end_pattern: Optional[str] = None,
    expected: Optional[bool] = True,
    starts_with: bool = False,
) -> List[str]:
    results = []
    spatterns = start_patterns.copy() if start_patterns else None
    start_pattern = spatterns.pop(0) if spatterns else None
    with open(filename, "r") as f:
        for line in f.readlines():
            if start_pattern and start_pattern and start_pattern in line:
                if spatterns != []:
                    start_pattern = spatterns.pop(0) if spatterns else None
                else:
                    start_pattern = None
            if end_pattern and end_pattern in line:
                break
            if not start_pattern and pattern in line:
                if exclude_pattern and starts_with and line.startswith(pattern):
                    line = "".join(line.split(pattern)[1:])
                elif exclude_pattern and pattern in line:
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
        dycore_timings = _grep(
            filename, " 0: fv_dynamics", exclude_pattern=True, expected=False
        )
        benchmark.fv_dyncore_timings = _extract_numerics(dycore_timings)

    # Get setup (grid, nodes)
    grid_stats_str = _grep(filename, "Resolution of dynamics restart")
    grid_stats = _extract_numerics(grid_stats_str)
    assert len(grid_stats) == 3
    benchmark.grid_resolution = (
        int(grid_stats[0]),
        int(grid_stats[1]),
        int(grid_stats[2]),
    )
    NX_str = _extract_numerics(
        _grep(filename, "Resource Parameter: NX:", exclude_pattern=True)
    )
    assert len(NX_str) == 1
    NX = int(NX_str[0])
    NY_str = _extract_numerics(
        _grep(filename, "Resource Parameter: NY:", exclude_pattern=True)
    )
    assert len(NY_str) == 1
    NY = int(NY_str[0])
    benchmark.node_setup = (NX, int(NY / 6), int(NX * (NY / 6) * 6))

    # Get details FV Grid Comp timings
    dyn_profiler_entry = "Times for component <DYN>"
    superdyn_profiler_entry = "Times for component <SUPERDYNAMICS>"
    dyn_profiler_patterns = [
        ("--------DYN_ANA", "DYN_ANA", "DYN"),
        ("--------DYN_PROLOGUE", "DYN_PROLOGUE", "DYN"),
        ("--------DYN_CORE", "DYN_CORE", "DYN"),
        ("----------PROLOGUE", "PROLOGUE", "DYN_CORE"),
        ("----------PULL_TRACERS", "PULL_TRACERS", "DYN_CORE"),
        ("----------STATE_TO_FV", "STATE_TO_FV", "DYN_CORE"),
        ("----------MAKE_NH", "MAKE_NH", "DYN_CORE"),
        ("----------MASS_FIX", "MASS_FIX", "DYN_CORE"),
        ("----------FV_DYNAMICS", "FV_DYNAMICS", "DYN_CORE"),
        ("----------PUSH_TRACERS", "PUSH_TRACERS", "DYN_CORE"),
        ("----------FV_TO_STATE", "FV_TO_STATE", "DYN_CORE"),
        ("--------DYN_EPILOGUE", "DYN_EPILOGUE", "DYN"),
    ]
    for pattern, shortname, parent in dyn_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=[dyn_profiler_entry],
                end_pattern=superdyn_profiler_entry,
                expected=False,
            )
        )
        if measures != []:
            benchmark.agcm_timings.append((shortname, measures[4], parent))

    # Get details for MOIST physics
    moist_profiler_entry = "Times for component <MOIST>"
    turbulence_profiler_entry = "Times for component <TURBULENCE>"
    moist_profiler_patterns = [
        ("------CONV_TRACERS", "CONV_TRACERS", "MOIST"),
        ("------AERO_ACTIVATE", "AERO_ACTIVATE", "MOIST"),
        ("------GF", "GF", "MOIST"),
        ("------UW", "UW", "MOIST"),
        ("------BACM_1M", "BACM_1M", "MOIST"),
    ]
    for pattern, shortname, parent in moist_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=[moist_profiler_entry],
                end_pattern=turbulence_profiler_entry,
                expected=False,
            )
        )
        if measures != []:
            benchmark.agcm_timings.append((shortname, measures[4], parent))

    # Get details for Turbulence physics
    chemenv_profiler_entry = "Times for component <CHEMENV>"
    turbulence_profiler_patterns = [
        ("--------REFRESHKS", "REFRESHKS", "TURBULENCE"),
        ("----------PRELIMS", "PRELIMS", "REFRESHKS"),
        ("----------MASSFLUX", "MASSFLUX", "REFRESHKS"),
        ("----------LOUIS", "LOUIS", "REFRESHKS"),
        ("----------LOCK", "LOCK", "REFRESHKS"),
        ("----------POSTLOCK", "POSTLOCK", "REFRESHKS"),
        ("----------BELJAARS", "BELJAARS", "REFRESHKS"),
        ("----------DECOMP", "DECOMP", "REFRESHKS"),
        ("--------DIFFUSE", "DIFFUSE", "TURBULENCE"),
    ]
    for pattern, shortname, parent in turbulence_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=[turbulence_profiler_entry],
                end_pattern=chemenv_profiler_entry,
                expected=False,
            )
        )
        if measures != []:
            benchmark.agcm_timings.append((shortname, measures[4], parent))

    # AGCM (for GEOS-FP)
    global_profiler_entry = "Model Throughput"
    global_profiler_entry_then_run = [global_profiler_entry, "--Run"]
    end_of_log_entry = "GEOSgcm Run Status"
    agcm_profiler_patterns = [
        ("------AGCM", "AGCM", ""),
        ("--------SUPERDYNAMICS", "SUPERDYNAMICS", "AGCM"),
        ("----------DYN", "DYN", "SUPERDYNAMICS"),
        ("--------PHYSICS", "PHYSICS", "AGCM"),
        ("----------GWD", "GWD", "PHYSICS"),
        ("----------MOIST", "MOIST", "PHYSICS"),
        ("----------TURBULENCE", "TURBULENCE", "PHYSICS"),
        ("----------CHEMISTRY", "CHEMISTRY", "PHYSICS"),
        ("------------CHEMENV", "CHEMENV", "CHEMISTRY"),
        ("------------HEMCO", "HEMCO", "CHEMISTRY"),
        ("------------PCHEM", "PCHEM", "CHEMISTRY"),
        ("------------ACHEM", "ACHEM", "CHEMISTRY"),
        ("------------GOCART", "GOCART", "CHEMISTRY"),
        ("------------GOCART2G", "GOCART2G", "CHEMISTRY"),
        ("------------TR", "TR", "CHEMISTRY"),
        ("----------SURFACE", "SURFACE", "PHYSICS"),
        ("------------SALTWATER", "SALTWATER", "SURFACE"),
        ("--------------SEAICETHERMO", "SEAICETHERMO", "SALTWATER"),
        ("--------------OPENWATER", "OPENWATER", "SALTWATER"),
        ("------------LAKE", "LAKE", "SURFACE"),
        ("------------LANDICE", "LANDICE", "SURFACE"),
        ("------------LAND", "LAND", "SURFACE"),
        ("--------------VEGDYN", "VEGDYN", "LAND"),
        ("--------------CATCH", "CATCH", "LAND"),
        ("----------RADIATION", "RADIATION", "PHYSICS"),
        ("------------SOLAR", "SOLAR", "RADIATION"),
        ("------------IRRAD", "IRRAD", "RADIATION"),
        ("------------SATSIM", "SATSIM", "RADIATION"),
        ("--------ORBIT", "ORBIT", "AGCM"),
    ]
    for pattern, shortname, parent in agcm_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=global_profiler_entry_then_run,
                end_pattern=end_of_log_entry,
                expected=False,
                starts_with=True,
            )
        )
        if measures != []:
            if shortname == "GOCART2G":
                # Bug reading the "2" as a measure
                benchmark.agcm_timings.append((shortname, measures[2], parent))
            elif shortname == "LAND":
                # Bug reading LANDICE in LAND
                benchmark.agcm_timings.append((shortname, measures[6], parent))
            else:
                benchmark.agcm_timings.append((shortname, measures[1], parent))

    # OGCM minus the AGCM tag (for GEOS-FP)
    global_profiler_entry = "Model Throughput"
    global_profiler_entry_then_run = [global_profiler_entry, "--Run"]
    end_of_log_entry = "GEOSgcm Run Status"
    ogcm_profiler_patterns = [
        ("------OGCM", "OGCM", ""),
        ("--------ORAD", "ORAD", "OGCM"),
        ("--------SEAICE", "SEAICE", "OGCM"),
        ("----------DATASEAICE", "DATASEAICE", "SEAICE"),
        ("--------OCEAN", "OCEAN", "OGCM"),
        ("----------DATASEA", "DATASEA", "OCEAN"),
    ]
    for pattern, shortname, parent in ogcm_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=global_profiler_entry_then_run,
                end_pattern=end_of_log_entry,
                expected=False,
                starts_with=True,
            )
        )
        if measures != []:
            if shortname == "DATASEA":
                # Bug reading DATASEA in DATASEAICE
                benchmark.ogcm_timings.append((shortname, measures[6], parent))
            elif shortname == "SEAICE":
                # Bug reading SEAICE in SEAICETHERMO
                benchmark.ogcm_timings.append((shortname, measures[6], parent))
            else:
                benchmark.ogcm_timings.append((shortname, measures[1], parent))

    # Full run
    global_profiler_entry = "Model Throughput"
    global_profiler_entry_then_run = [global_profiler_entry, "--Run"]
    end_of_log_entry = "GEOSgcm Run Status"
    run_profiler_patterns = [
        ("--Run", "RUN", ""),
        ("----EXTDATA", "EXTDATA", "RUN"),
        ("----GCM", "GCM", "RUN"),
        ("------AIAU", "AIAU", "GCM"),
        ("------ADFI", "ADFI", "GCM"),
        ("----HIST", "HIST", "RUN"),
    ]
    for pattern, shortname, parent in run_profiler_patterns:
        measures = _extract_numerics(
            _grep(
                filename,
                pattern,
                start_patterns=global_profiler_entry_then_run,
                end_pattern=end_of_log_entry,
                expected=False,
                starts_with=True,
            )
        )
        if measures != []:
            benchmark.run_timings.append((shortname, measures[1], parent))

    # Model throughput
    global_init_time = _grep(
        filename, "--Initialize", start_patterns=[global_profiler_entry]
    )
    benchmark.global_init_time = _extract_numerics(global_init_time)[1]
    global_run_time = _grep(filename, "--Run", start_patterns=[global_profiler_entry])
    benchmark.global_run_time = _extract_numerics(global_run_time)[1]
    global_finalize_time = _grep(
        filename, "--Finalize", start_patterns=[global_profiler_entry]
    )
    benchmark.global_finalize_time = _extract_numerics(global_finalize_time)[1]

    return benchmark


if __name__ == "__main__":
    import sys

    benchmark_data = parse_geos_log(sys.argv[1])
    print(benchmark_data)
    benchmark_data.plot_run("./RUN.png")
