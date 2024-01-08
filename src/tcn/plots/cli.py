import tcn.plots.geos.dash_grid_heatmaps as dash
from tcn.plots.geos.plot_via_plotly import plot_heatmaps_mean_on_K
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
def heatmap(input_nc4: str, variable: str, dimensions: List[str]):
    nc_data = xr.open_mfdataset(input_nc4)
    plot_heatmaps_mean_on_K(
        dataset=nc_data,
        variable=variable,
        write=True,
        mean_dims=list(dimensions) or None,
    )


cli.add_command(dash_compare)
cli.add_command(heatmap)
