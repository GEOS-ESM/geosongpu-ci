from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import plotly.express as px


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
