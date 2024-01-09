import logging
import sys

import plotly.express as px
import plotly.graph_objects as pgo
import xarray as xr

from typing import List, Optional, Tuple


def merge_variable(directory: str, variable: str):
    logging.log(logging.WARN, "Real slow! Better to use ncrcat from NCO suite")
    ds = xr.open_mfdataset(f"{directory}/**/*.nc4", combine="by_coords")
    ds[variable].to_netcdf(f"merged_{variable}.netcdf4")


def _auto_detect_dimensions(dataset: xr.Dataset, variable: str):
    dims = []
    # Do we have a "tile" dims
    find_tile = [k for k in dataset[variable].dims if "tile" in str(k)]
    if len(find_tile) == 1:
        dims.append(str(find_tile[0]))
    # Time
    dims.append("time")
    # Do we have a K dim (try "z" or "lev")
    find_z = [k for k in dataset[variable].dims if "z" in str(k) or "lev" in str(k)]
    if len(find_z) == 1:
        dims.append(str(find_z[0]))
    return dims


def _mean_on_dims(
    dataset: xr.Dataset,
    variable: str,
    dims: Optional[List[str]] = None,
    select_time: int = -1,
) -> Tuple[xr.DataArray, List[str]]:
    dims = (
        _auto_detect_dimensions(
            dataset,
            variable,
        )
        if not dims
        else dims
    )
    d_var = dataset[variable]
    if select_time >= 0:
        if "time" in dims:
            dims.pop(dims.index("time"))
        d_var = d_var.isel(time=select_time)
    return d_var.mean(dims), dims


def nc4_to_xarray(nc4_file: str) -> xr.Dataset:
    return xr.open_mfdataset(nc4_file)


def plot(
    dataset: xr.Dataset,
    variable: str,
    write=False,
    plot_verb: Optional[str] = None,
    mean_dims: Optional[List[str]] = None,
    dataset_B: Optional[xr.Dataset] = None,
    select_time: int = -1,
):
    # Average dataset over dims
    array_A, dims = _mean_on_dims(
        dataset=dataset,
        variable=variable,
        dims=mean_dims,
        select_time=select_time,
    )

    # Optionally do a diff with another dataset
    if dataset_B:
        array_B, _unused = _mean_on_dims(
            dataset=dataset_B,
            variable=variable,
            dims=dims,
            select_time=select_time,
        )
        array = array_B - array_A
    else:
        array = array_A

    # Plot
    if plot_verb == "heatmap" or len(array.dims) == 2:
        plot_verb = "heatmap"
        fig = px.imshow(array, color_continuous_scale="RdBu_r")
    elif plot_verb == "line" or len(array.dims) == 1:
        plot_verb = "line"
        fig = pgo.Figure(data=pgo.Scatter(y=array))
    else:
        fig = None
        RuntimeError(
            f"Uncapable of plotting verb: {plot_verb} or dims count {array.dims}"
        )

    # Write
    if fig and write:
        dims_as_str = ("__averaged_over_" + "_".join(dims)) if dims else ""
        postfix = "__DIFF" if dataset_B else ""
        postfix += f"__t{select_time}" if select_time >= 0 else ""
        filename = f"{plot_verb}{dims_as_str}__of_{variable}{postfix}.png"
        print(f"Writing {filename}")
        fig.write_image(filename)

    return fig


if __name__ == "__main__":
    nc4_file = sys.argv[1]
    variable = sys.argv[2]
    plot(
        dataset=nc4_to_xarray(nc4_file),
        variable=variable,
        write=True,
    )
