import numpy as np
from typing import Dict, Any
import geosongpu_ci.tools.hws.constants as cst
import dataclasses
from geosongpu_ci.tools.hws.constants import (
    HWS_HW_CPU,
)


@dataclasses.dataclass
class EnergyReport:
    CPU_envelop_integrated: float = 0  # kW * sample_count
    CPU_envelop_kWh: float = 0
    GPU_envelop_integrated: float = 0  # kW * sample_count
    GPU_envelop_kWh: float = 0
    overall_envelop_integrated: float = 0  # kW * sample_count
    overall_envelop_kWh: float = 0


def energy_envelop_calculation(
    cpu_psu_data: np.ndarray,
    gpu_psu_data: np.ndarray,
    cpu_label: str = HWS_HW_CPU,
    verbose: bool = True,
) -> EnergyReport:
    report = EnergyReport()
    # TODO we need the sample rate here too
    sample_count = len(cpu_psu_data)

    # Grab integrated power using trapezoide integration on all samples
    report.GPU_envelop_integrated = np.trapz(gpu_psu_data / 1000)
    report.CPU_envelop_integrated = np.trapz(cpu_psu_data / 1000)
    report.overall_envelop_integrated = (
        report.GPU_envelop_integrated + report.CPU_envelop_integrated
    )

    # Average kWh calculation
    # TODO: Wrong?!
    sampling_time_hours_default = (
        (sample_count - 1) * cst.DEFAULT_SAMPLERATE_IN_S / (60 * 60)
    )
    report.overall_envelop_kWh = (
        report.overall_envelop_integrated / sample_count
    ) / sampling_time_hours_default
    report.CPU_envelop_kWh = (
        report.CPU_envelop_integrated / sample_count
    ) / sampling_time_hours_default
    report.GPU_envelop_kWh = (
        report.GPU_envelop_integrated / sample_count
    ) / sampling_time_hours_default

    if verbose:
        print(
            f"Number of samples: {sample_count}\n"
            f"CPU envelop:{report.CPU_envelop_integrated:.0f} kW.sample_count\n"
            f"CPU envelop (@ default sample rate): {report.CPU_envelop_kWh:.2f} kW/h\n"
            f"GPU envelop:{report.GPU_envelop_integrated:.0f} kW.sample_count\n"
            f"GPU envelop (@ default sample rate): {report.GPU_envelop_kWh:.2f} kW/h\n"
            f"Overall envelop: {report.overall_envelop_integrated:.0f} kW.sample_count\n"
            f"Overall envelop (@ default sample rate): {report.overall_envelop_kWh:.2f} kW/h"
        )

    return report


def load_data(
    data_filepath: str,
    data_format: str = "npz",
) -> Dict[str, Any]:
    if data_format != "npz":
        raise NotImplementedError(f"Format {data_format} not implemented for graphing")
    return np.load(data_filepath)
