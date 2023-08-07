from matplotlib import pyplot
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
    d = load_data(data_filepath, data_format)
    n = len(d["cpu_psu"])
    s = slice(0, n)
    print(n, s)
    yd = np.arange(len(d["cpu_psu"][s]))

    fig, ax1 = pyplot.subplots(figsize=(8, 8))
    ax2 = pyplot.twinx()

    ax1.plot(yd, d["gpu_psu"][s], label="GPU PSU(W)", linewidth=0.5)
    ax1.plot(yd, d["gpu_exe_utl"][s], label="GPU Utilization(%)", linewidth=0.5)
    ax2.plot(yd, d["gpu_mem"][s], label="GPU VRAM(Mb)", color=COLOR_VRAM, linewidth=0.5)
    ax1.plot(yd, d["cpu_psu"][s], label="CPU PSU(W - extrapolated)", linewidth=0.5)
    ax1.plot(yd, d["cpu_exe_utl"][s], label="CPU Utilization(%)", linewidth=0.5)

    ax1.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        fancybox=True,
        shadow=True,
    )
    ax1.set_ylabel("W/%", fontsize=10)
    ax1.set_ylim(0, HWS_HARDWARE_SPECS[HWS_HW_GPU]["PSU_TDP"])

    ax2.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.05),
        ncol=3,
        fancybox=True,
        shadow=True,
    )
    ax2.set_ylabel("Mb", color=COLOR_VRAM, fontsize=10)
    ax2.tick_params(axis="y", labelcolor="C4")
    ax2.set_ylim(0, HWS_HARDWARE_SPECS[HWS_HW_GPU]["MAX_VRAM"])

    fig.savefig(data_filepath.replace(f".{data_format}", ""))

    gpu_kW_envelop, cpu_kW_envelop = energy_envelop_calculation(
        d["cpu_psu"][s], d["gpu_psu"][s]
    )
    print(
        f"Overall CPU W usage:{cpu_kW_envelop:.0f} kW\n",
        f"Overall GPU W usage:{gpu_kW_envelop:.0f} kW",
    )
