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
@cli.argument("command")
def client(command: str):
    hws_client.cli(command)


@cli.command()
def graph():
    hws_graph.cli()


if __name__ == "__main__":
    cli()
