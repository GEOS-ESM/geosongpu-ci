from dataclasses import dataclass, field
from typing import Tuple, Iterable, List


@dataclass
class BenchmarkRawData:
    backend: str = ""
    grid_resolution: Tuple[int, int, int] = (0, 0, 0)  # nx / ny / nz
    node_setup: Tuple[int, int, int] = (0, 0, 0)  # NX / NY / Total ranks used
    global_run_time: float = 0  # seconds fort the global RUN
    fv_dyncore_timings: Iterable[float] = field(default_factory=list)  # seconds
    inner_dycore_timings: Iterable[float] = field(default_factory=list)  # seconds
    fv_gridcomp_detailed_profiling: List[Tuple[str, float]] = field(
        default_factory=list
    )