import click
import geosongpu_ci.tools.hws.server as hws_server
import geosongpu_ci.tools.hws.client as hws_client
import geosongpu_ci.tools.hws.graph as hws_graph


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


if __name__ == "__main__":
    cli()
