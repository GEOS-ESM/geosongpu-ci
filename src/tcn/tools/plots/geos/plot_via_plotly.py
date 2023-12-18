import sys

import plotly.express as px
import plotly.graph_objects as pgo
import xarray as xr


def merge_variable(directory: str, variable: str):
    """Real slow! Better to use ncrcat from NCO suite"""
    ds = xr.open_mfdataset(f"{directory}/**/*.nc4", combine="by_coords")
    ds[variable].to_netcdf(f"merged_{variable}.netcdf4")


def plot_contour_mean_dtime_dlon(nc4_file: str, variable: str):
    ds = xr.open_mfdataset(nc4_file)
    ds_mean_dt_dlat = ds[variable].mean(["time", "lon"])

    fig = pgo.Figure(data=pgo.Contour(z=ds_mean_dt_dlat))
    fig.write_image(f"time_lat_averaged_of_{variable}.png")


def plot_line_mean_dtime_dlon(nc4_file: str, variable: str):
    ds = xr.open_mfdataset(nc4_file)
    ds_mean_dt_dlat = ds[variable].mean(["time", "lon"])

    fig = pgo.Figure(data=pgo.Scatter(y=ds_mean_dt_dlat))
    fig.write_image(f"time_lat_averaged_of_{variable}.png")


def plot_heatmaps_mean_on_K(dataset: xr.Dataset, variable: str, write=False):
    find_z = [k for k in dataset[variable].dims if "z" in str(k)]
    assert len(find_z) == 1
    ds_mean_dt_K = dataset[variable].mean(["tile", "time", find_z[0]])
    fig = px.imshow(ds_mean_dt_K, color_continuous_scale="RdBu_r")
    if write:
        fig.write_image(f"heatmap__time_K_averaged_of_{variable}.png")
    return fig


def plot_heatmaps_diff_mean_on_K(
    dataset_checked: xr.Dataset,
    dataset_reference: xr.Dataset,
    variable: str,
    write=False,
) -> pgo.Figure:
    find_z = [k for k in dataset_checked[variable].dims if "z" in str(k)]
    assert len(find_z) == 1
    ds_mean_dt_K = (dataset_checked[variable] - dataset_reference[variable]).mean(
        ["tile", "time", find_z[0]]
    )
    ds_ref_meand_dt_K = dataset_reference[variable].mean(["tile", "time", find_z[0]])
    zmax = float(ds_ref_meand_dt_K.max().values)
    zmin = float(ds_ref_meand_dt_K.min().values)
    zmax_range = max(abs(zmax), abs(zmin))
    fig = px.imshow(
        ds_mean_dt_K,
        color_continuous_scale="RdBu_r",
        zmax=zmax_range,
        zmin=-zmax_range,
    )
    if write:
        fig.write_image(f"heatmap_diff__time_K_averaged_of_{variable}.png")
    return fig


def diff_dataset(A: xr.Dataset, B: xr.Dataset, variable):
    return A[variable] - B[variable]


def nc4_to_xarray(nc4_file: str) -> xr.Dataset:
    return xr.open_mfdataset(nc4_file)


if __name__ == "__main__":
    # merge_variable("/home/fgdeconi/work/git/geosongpu-ci/tmp/AQ_OUTPUT", "U")
    nc4_file = sys.argv[1]
    variable = sys.argv[2]
    plot_type = sys.argv[3]
    if plot_type == "contour":
        plot_contour_mean_dtime_dlon(nc4_file, variable)
    elif plot_type == "line":
        plot_line_mean_dtime_dlon(nc4_file, variable)
    elif plot_type == "heatmap_3d":
        plot_heatmaps_mean_on_K(nc4_to_xarray(nc4_file), variable, write=True)
    else:
        raise NotImplementedError(f"Plot {plot_type} unimplemented")
