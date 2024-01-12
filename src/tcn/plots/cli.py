import tcn.plots.geos.dash_grid_heatmaps as dash
from tcn.plots.geos.plot_via_plotly import plot as plotly_plot
import xarray as xr
import click
from typing import List


@click.group()
def cli():
    pass


@click.command()
@click.argument("reference_nc4", type=str)
@click.argument("computed_nc4", type=str)
def dash_compare(reference_nc4: str, computed_nc4: str):
    dash.spin(reference_nc4, computed_nc4)


@click.command()
@click.argument("input_nc4", type=str)
@click.argument("variable", type=str)
@click.option("--dimensions", "-d", multiple=True, type=str)
@click.option("--diff_with", "-dw", type=str)
@click.option("--select_time", "-st", type=int, default=-1)
def plot(
    input_nc4: str,
    variable: str,
    dimensions: List[str],
    diff_with: str,
    select_time: int,
):
    nc_data = xr.open_mfdataset(input_nc4)
    nc_B_data = xr.open_mfdataset(diff_with) if diff_with else None
    plotly_plot(
        dataset=nc_data,
        variable=variable,
        write=True,
        mean_dims=list(dimensions) or None,
        dataset_B=nc_B_data,
        select_time=select_time,
    )


cli.add_command(dash_compare)
cli.add_command(plot)
