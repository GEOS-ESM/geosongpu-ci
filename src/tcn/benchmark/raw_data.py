from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


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
