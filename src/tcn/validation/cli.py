import click
from tcn.validation.analysis import analysis
import tcn.validation.serialbox.serialbox_dat_to_netcdf as sdnc
import xarray as xr


@click.group()
def cli():
    pass


@click.command()
@click.argument("reference_nc4", type=str)
@click.argument("computed_nc4", type=str)
@click.argument("variable", type=str)
@click.option("--select_time", "-st", type=int, default=0)
def validate(
    reference_nc4: str,
    computed_nc4: str,
    variable: str,
    select_time: int = 0,
):
    analysis(
        ref_dataset=xr.open_mfdataset(reference_nc4),
        cpu_dataset=xr.open_mfdataset(computed_nc4),
        variable=variable,
        time=select_time,
    )


@click.command()
@click.argument("data_path_of_dat", type=str)
@click.argument("output_path", type=str)
@click.option("--rank", "-r", type=int, default=-1)
@click.option("--savepoint", "-s", type=int, default=-1)
def serialbox(
    data_path_of_dat: str,
    output_path: str,
    rank: int,
    savepoint: int,
):
    sdnc.main(
        data_path=data_path_of_dat,
        output_path=output_path,
        do_only_rank=rank,
        do_only_savepoint=savepoint,
    )


cli.add_command(validate)
cli.add_command(serialbox)
