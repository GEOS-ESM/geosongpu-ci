from tcn.benchmark.geos_log_parser import parse_geos_log
from tcn.benchmark.report import report

if __name__ == "__main__":
    import sys

    raw_data = []
    for log in sys.argv[1:]:
        raw_data.append(parse_geos_log(log))

    benchmark_report = report(raw_data)
    print(benchmark_report)
