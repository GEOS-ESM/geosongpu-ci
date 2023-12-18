import tcn.tools.plots.geos.dash_grid_heatmaps as dash


def cli():
    import sys

    reference_nc = sys.argv[1]
    dsl_nc = sys.argv[2]
    dash.spin(reference_nc, dsl_nc)


if __name__ == "__main__":
    cli()
