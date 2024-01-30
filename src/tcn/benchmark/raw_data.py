import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional
import plotly.express as px
from tcn.benchmark.string_trf import extract_numerics


@dataclass
class BenchmarkRawData:
    backend: str = ""
    grid_resolution: Tuple[int, int, int] = (0, 0, 0)  # nx / ny / nz
    node_setup: Tuple[int, int, int] = (0, 0, 0)  # NX / NY / Total ranks used
    global_init_time: float = 0  # seconds fort the global INITIALIZE
    global_run_time: float = 0  # seconds fort the global RUN
    global_finalize_time: float = 0  # seconds fort the global FINALIZE
    fv_dyncore_timings: List[float] = field(default_factory=list)  # seconds
    inner_dycore_timings: List[float] = field(default_factory=list)  # seconds
    fv_gridcomp_detailed_profiling: List[Tuple[str, float, str]] = field(
        default_factory=list
    )
    # AGCM only
    agcm_timings: List[Tuple[str, float, str]] = field(default_factory=list)
    # OGCM omly
    ogcm_timings: List[Tuple[str, float, str]] = field(default_factory=list)
    # All run items without AGCM or OGCM
    run_timings: List[Tuple[str, float, str]] = field(default_factory=list)
    timings: List[Tuple[str, float, str]] = field(default_factory=list)
    hws_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def backend_sanitized(self):
        """Generate a filname-safe backend name"""

        return (
            self.backend.replace("(", "")
            .replace(": ", "-")
            .replace(":", "-")
            .replace(" ", "-")
            .replace(")", "-")
        )

    def _sunburst_plot(self, data, path: str):
        fig = px.sunburst(data, names="comps", parents="parents", values="values")
        fig = px.sunburst(
            data,
            names="comps",
            parents="parents",
            values="values",
            branchvalues="total",
        )
        fig.write_image(path, width=800, height=800)
        fig.write_html(path[:-3] + "html")

    def parse_geos_log_summary(self, filename: str):
        parents: List[Tuple[str, int]] = []
        start_patterns = ["Model Throughput", "All"]
        start_pattern: Optional[str] = start_patterns.pop(0)
        end_pattern = "GEOSgcm Run Status: 0"
        with open(filename, "r") as f:
            for line in f.readlines():
                # Skip until parsing
                if start_pattern and start_pattern and start_pattern in line:
                    if start_patterns != []:
                        start_pattern = start_patterns.pop(0)
                    else:
                        start_pattern = None
                # Parsing is done
                if end_pattern and end_pattern in line:
                    break
                # Parse result line
                if not start_pattern:
                    name_and_hierarchy = line.split(" ")[0]
                    timings = " ".join(line.split(" ")[1:])
                    hierarchy_level = len(name_and_hierarchy) - len(
                        name_and_hierarchy.lstrip("-")
                    )
                    name = name_and_hierarchy.lstrip("-")
                    time = extract_numerics([timings])[1]
                    parent = ""
                    if len(parents) > 0 and parents[-1][1] < hierarchy_level:
                        parent = parents[-1][0]
                    else:
                        while len(parents) > 0 and parents[-1][1] >= hierarchy_level:
                            parents.pop()
                        parent = parents[-1][0] if len(parents) else ""
                    parents.append((name, hierarchy_level))
                    self.timings.append((name, time, parent))

    def plot_agcm(self, path: str):
        comps = []
        parents = []
        values = []
        for name, time, parent in self.agcm_timings:
            comps.append(name)
            values.append(time)
            parents.append(parent)
        data = dict(comps=comps, parents=parents, values=values)
        self._sunburst_plot(data, path)

    def plot_ogcm(self, path: str):
        comps = []
        parents = []
        values = []
        for name, time, parent in self.ogcm_timings:
            comps.append(name)
            values.append(time)
            parents.append(parent)
        data = dict(comps=comps, parents=parents, values=values)
        self._sunburst_plot(data, path)

    def plot_run(self, path: str):
        comps = []
        parents = []
        values = []
        for name, time, parent in self.run_timings:
            comps.append(name)
            values.append(time)
            parents.append(parent)
        for name, time, parent in self.agcm_timings:
            if name == "AGCM":
                parent = "GCM"
            comps.append(name)
            values.append(time)
            parents.append(parent)
        for name, time, parent in self.ogcm_timings:
            if name == "OGCM":
                parent = "GCM"
            comps.append(name)
            values.append(time)
            parents.append(parent)
        data = dict(comps=comps, parents=parents, values=values)
        self._sunburst_plot(data, path)

    def plot_all(self, path: str):
        comps = []
        parents = []
        values = []
        prefix = ""
        for name, time, parent in self.timings:
            # Sunburst doesn't allow for duplicates so
            # we have to prefix names and parents
            if name == "SetService":
                prefix = "s"
            if name == "Initialize":
                prefix = "i"
            if name == "Run":
                prefix = "r"
            if name == "Finalize":
                prefix = "f"
            comps.append(prefix + name)
            values.append(time)
            if parent == "All":
                parents.append(parent)
            else:
                parents.append(prefix + parent)
        data = dict(comps=comps, parents=parents, values=values)
        self._sunburst_plot(data, path)


if __name__ == "__main__":
    bench = BenchmarkRawData()
    bench.parse_geos_log_summary(sys.argv[1])
    bench.plot_all("./model_breakdown.png")
