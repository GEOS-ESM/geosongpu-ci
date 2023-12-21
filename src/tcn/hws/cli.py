from typing import Optional, Tuple

import click

import tcn.hws.client as hws_client
import tcn.hws.constants as cst
import tcn.hws.graph as hws_graph
import tcn.hws.server as hws_server


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)


@cli.command()
def server():
    hws_server.cli()


@cli.command()
@click.argument("command")
@click.option("--name", default="hws", help="[dump] Filename for the .npz dump")
def client(command: str, name: str):
    hws_client.cli(command, name)


@cli.command()
@click.argument("data_filepath")
def graph(data_filepath: str):
    hws_graph.cli(data_filepath)


@cli.command()
@click.argument("data_filepath")
@click.option("--data_range", nargs=2, type=float)
def envelop(
    data_filepath: str, data_range: Optional[Tuple[float, float]]
):  # TODO: this should be saved in a header in the data file
    dt = cst.CLIENT_CMDS[cst.CLIENT_CMD_START]["dt"]
    if data_range:
        range_start, range_stop = data_range
        range_start = int(range_start / dt)
        range_stop = int(range_stop / dt)
        hws_graph.cli(data_filepath, data_range=slice(range_start, range_stop))
    else:
        hws_graph.cli(data_filepath)


if __name__ == "__main__":
    cli()
