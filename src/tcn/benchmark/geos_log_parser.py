import sys

from tcn.benchmark.benchmark import Benchmark
from tcn.benchmark.string_trf import extract_numerics, grep


def parse_geos_log(filename: str) -> Benchmark:
    benchmark = Benchmark()

    # Get backend
    is_gtfv3 = grep(filename, "RUN_GTFV3:1", exclude_pattern=True, expected=False) != []
    if not is_gtfv3:
        benchmark.backend = "fortran"
    else:
        backend_pattern = "backend : "
        grepped = grep(filename, backend_pattern, exclude_pattern=True, expected=False)
        if grepped == []:
            benchmark.backend = "gtfv3 (details failed to parse)"
        else:
            backend = grepped[0].strip().replace("\n", "").replace(":", "")
            benchmark.backend = f"gtfv3_{backend}"

    # Get timings of FV
    if is_gtfv3:
        interface_timings = grep(filename, " 0 , geos_gtfv3", exclude_pattern=True)
        benchmark.fv_dyncore_timings = extract_numerics(interface_timings)

        if "dace" in benchmark.backend:
            dycore_timings = grep(
                filename, "] Run...", exclude_pattern=True, expected=False
            )
            benchmark.inner_dycore_timings = extract_numerics(dycore_timings)
    else:
        dycore_timings = grep(
            filename, " 0: fv_dynamics", exclude_pattern=True, expected=False
        )
        benchmark.fv_dyncore_timings = extract_numerics(dycore_timings)

    # Get setup (grid, nodes)
    grid_stats_str = grep(filename, "Resolution of dynamics restart")
    grid_stats = extract_numerics(grid_stats_str)
    assert len(grid_stats) == 3
    benchmark.grid_resolution = (
        int(grid_stats[0]),
        int(grid_stats[1]),
        int(grid_stats[2]),
    )
    NX_str = extract_numerics(
        grep(filename, "Resource Parameter: NX:", exclude_pattern=True)
    )
    assert len(NX_str) == 1
    NX = int(NX_str[0])
    NY_str = extract_numerics(
        grep(filename, "Resource Parameter: NY:", exclude_pattern=True)
    )
    assert len(NY_str) == 1
    NY = int(NY_str[0])
    benchmark.node_setup = (NX, int(NY / 6), int(NX * (NY / 6) * 6))

    # Model throughput
    global_profiler_entry = "Model Throughput"
    global_init_time = grep(
        filename, "--Initialize", start_patterns=[global_profiler_entry]
    )
    benchmark.global_init_time = extract_numerics(global_init_time)[1]
    global_run_time = grep(filename, "--Run", start_patterns=[global_profiler_entry])
    benchmark.global_run_time = extract_numerics(global_run_time)[1]
    global_finalize_time = grep(
        filename, "--Finalize", start_patterns=[global_profiler_entry]
    )
    benchmark.global_finalize_time = extract_numerics(global_finalize_time)[1]

    #
    # WARNING - THIS IS A BESPOKE PARSE. THIS HAS BEEN REPLACED
    #           BY A GENERIC PARSER IN BENCHMARKDATA
    #

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
        measures = extract_numerics(
            grep(
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
        measures = extract_numerics(
            grep(
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
        measures = extract_numerics(
            grep(
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
        measures = extract_numerics(
            grep(
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
        measures = extract_numerics(
            grep(
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
        measures = extract_numerics(
            grep(
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

    return benchmark


if __name__ == "__main__":
    benchmark_data = parse_geos_log(sys.argv[1])
    # print(benchmark_data)
    benchmark_data.plot_all("./GEOS-FP.png")
