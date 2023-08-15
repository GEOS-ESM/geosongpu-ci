import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from geosongpu_ci.tools.hws.constants import (
    HWS_HW_GPU,
    HWS_HARDWARE_SPECS,
)
from typing import Dict, Any

COLOR_VRAM = "C4"


def energy_envelop_calculation(cpu_psu_data: np.ndarray, gpu_psu_data: np.ndarray):
    gpu_kW_envelop = np.trapz(gpu_psu_data / 1000)
    cpu_kW_envelop = np.trapz(cpu_psu_data / 1000)
    return gpu_kW_envelop, cpu_kW_envelop


def load_data(
    data_filepath: str,
    data_format: str = "npz",
) -> Dict[str, Any]:
    if data_format != "npz":
        raise NotImplementedError(f"Format {data_format} not implemented for graphing")
    return np.load(data_filepath)


def cli(
    data_filepath: str,
    data_format: str = "npz",
    dynamic_gpu_load: bool = True,
):
    # TODO: implement a dynamic read of when the GPU "kicks in"
    d = load_data(data_filepath, data_format)
    n = len(d["cpu_psu"])
    s = slice(0, n)
    yd = np.arange(len(d["cpu_psu"][s]))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Add traces
    fig.add_trace(
        go.Scatter(y=d["gpu_psu"][s], x=yd, name="GPU PSU(W)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["gpu_exe_utl"][s], x=yd, name="GPU Utilization(%)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["cpu_psu"][s], x=yd, name="CPU PSU(W - extrapolated)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["cpu_exe_utl"][s], x=yd, name="CPU Utilization(%)"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(y=d["gpu_mem"][s], x=yd, name="GPU VRAM (Mb)"),
        secondary_y=True,
    )

    # Labels
    fig.update_layout(
        title_text="Hardware sensors",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Sample #")
    fig.update_yaxes(
        title_text="W or %",
        secondary_y=False,
        range=[0, HWS_HARDWARE_SPECS[HWS_HW_GPU]["PSU_TDP"]],
    )
    fig.update_yaxes(
        title_text="Mb",
        secondary_y=True,
        range=[0, HWS_HARDWARE_SPECS[HWS_HW_GPU]["MAX_VRAM"]],
    )

    fig.write_image(data_filepath.replace(f".{data_format}", ".png"))

    gpu_kW_envelop, cpu_kW_envelop = energy_envelop_calculation(
        d["cpu_psu"][s], d["gpu_psu"][s]
    )
    print(
        f"Overall CPU W usage:{cpu_kW_envelop:.0f} kW\n",
        f"Overall GPU W usage:{gpu_kW_envelop:.0f} kW",
    )


# Useful for debug
if __name__ == "__main__":
    import sys

    cli(sys.argv[1])
