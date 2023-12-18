import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tcn.tools.hws.analysis import energy_envelop_calculation, load_data
from tcn.tools.hws.constants import HWS_HARDWARE_SPECS, HWS_HW_CPU, HWS_HW_GPU

COLOR_VRAM = "C4"


def cli(
    data_filepath: str,
    data_format: str = "npz",
    data_range: slice = slice(None),
    cpu_label: str = HWS_HW_CPU,
    gpu_label: str = HWS_HW_GPU,
):
    d = load_data(data_filepath, data_format)
    sample_count = len(d["cpu_psu"][data_range])
    yd = np.arange(sample_count)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Add traces
    fig.add_trace(
        go.Scatter(y=d["gpu_psu"][data_range], x=yd, name="GPU PSU(W)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["gpu_exe_utl"][data_range], x=yd, name="GPU Utilization(%)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["cpu_psu"][data_range], x=yd, name="CPU PSU(W - extrapolated)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(y=d["cpu_exe_utl"][data_range], x=yd, name="CPU Utilization(%)"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(y=d["gpu_mem"][data_range], x=yd, name="GPU VRAM (Mb)"),
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
        range=[0, HWS_HARDWARE_SPECS[gpu_label]["PSU_TDP"]],
    )
    fig.update_yaxes(
        title_text="Mb",
        secondary_y=True,
        range=[0, HWS_HARDWARE_SPECS[gpu_label]["MAX_VRAM"]],
    )

    print(
        f"Max VRAM: {np.max(d['gpu_mem'][data_range])}\n"
        f"Max GPU PSU: {np.max(d['gpu_psu'][data_range])}\n"
        f"Max CPU exe: {np.max(d['gpu_exe_utl'][data_range])}\n"
    )

    fig.write_image(data_filepath.replace(f".{data_format}", ".png"))

    energy_envelop_calculation(d["cpu_psu"][data_range], d["gpu_psu"][data_range])


# Useful for debug
if __name__ == "__main__":
    import sys

    cli(sys.argv[1])
