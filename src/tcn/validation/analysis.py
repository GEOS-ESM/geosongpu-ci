import xarray as xr
import plotly.express as px
from typing import Optional
import numpy as np


def analysis(
    ref_dataset: xr.Dataset,
    cpu_dataset: xr.Dataset,
    variable: Optional[str],
    time: int = 0,
):
    for name in list(ref_dataset.keys()):
        if variable and variable == name:
            ref_var = ref_dataset[name].isel(time=time)
            cpu_var = cpu_dataset[name].isel(time=time)
            diff = (cpu_var - ref_var).values.flatten()
            diff = diff[~np.isnan(diff)]
            print(f"{name}:\n  " f"Max: {diff.max():.2f}\n" f"  Min: {diff.min():.2f}")

            var_name = ref_var.attrs["long_name"].replace("_", " ").title()
            fig = px.histogram(
                x=diff,
                log_y=True,
            )
            fig.update_layout(
                title=f"{var_name} ({name})",
                xaxis_title=f"Difference in {ref_var.attrs['units']}",
            )
            fig.write_image(f"{name}_hist.png")


if __name__ == "__main__":
    import sys

    ref_dataset = xr.open_mfdataset(sys.argv[1])
    cpu_dataset = xr.open_mfdataset(sys.argv[2])
    var = sys.argv[3]
    analysis(
        ref_dataset,
        cpu_dataset,
        variable=var,
    )
