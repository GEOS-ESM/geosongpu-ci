from matplotlib import pyplot
import numpy as np
from geosongpu_ci.tools.hws.constants import (
    HWS_HWLOAD_FILENAME,
    HWS_HARDWARE_SPECS,
    HWS_HW_GPU,
)

COLOR_VRAM = "C4"


def cli(dump_format="npz", dynamic_gpu_load=True):
    if dump_format != "npz":
        raise NotImplementedError(f"Format {dump_format} not implemented for graphing")
    d = np.load(f"{HWS_HWLOAD_FILENAME}.npz")
    n = len(d["cpu_psu"])
    s = slice(n - 5000, n)
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

    fig.savefig("Hardware_Load")

    print(
        f" Overall GPU W usage:{np.trapz(d['gpu_psu'][s]/1000):.0f} kW\n",
        f"Overall CPU W usage:{np.trapz(d['cpu_psu'][s]/1000):.0f} kW",
    )
