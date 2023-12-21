import pathlib

import dash_bootstrap_components as dbc
import xarray as xr
from dash import Dash, Input, Output, dcc, html

import tcn.plots.geos.plot_via_plotly as ph

app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
reference_nc = ""
dsl_nc = ""


def diff_plots(reference, candidate):
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(
            ph.plot_heatmaps_diff_mean_on_K(candidate, reference, variable=str(c))
        )
    return figs


def ref_plots(reference, candidate):
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(ph.plot_heatmaps_mean_on_K(reference, variable=str(c)))
    return figs


def dsl_plots(reference, candidate):
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(ph.plot_heatmaps_mean_on_K(candidate, variable=str(c)))
    return figs


def serve_layout():
    return dbc.Container(
        [
            dcc.Store(id="store"),
            html.H1("Dynamical core State"),
            html.Hr(),
            dbc.Button(
                "Reload graphs",
                color="primary",
                id="button",
                className="mb-3",
            ),
            dbc.Tabs(
                [
                    dbc.Tab(label="Difference", tab_id="diff"),
                    dbc.Tab(label="Reference", tab_id="ref"),
                    dbc.Tab(label="DSL", tab_id="dsl"),
                ],
                id="tabs",
                active_tab="diff",
            ),
            html.Div(id="tab-content", className="p-4"),
        ]
    )


app.layout = serve_layout


@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("store", "data")],
)
def render_tab_content(active_tab, data):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    header_row = None
    if active_tab == "diff":
        header_row = dbc.Row(
            dbc.Alert("Differnce plot scale is 1%% of max range", color="info")
        )

    if active_tab:
        return [
            header_row,
            dbc.Row([dbc.Col(dcc.Graph(figure=fig), width=6) for fig in data]),
        ]
    return "No tab selected"


@app.callback(
    Output("store", "data"),
    [
        Input("tabs", "active_tab"),
        Input("button", "n_clicks"),
    ],
)
def get_graphs(active_tab, _n):
    """
    This callback generates data
    """
    global reference_nc
    reference = xr.open_mfdataset(pathlib.Path(reference_nc))
    global dsl_nc
    candidate = xr.open_mfdataset(pathlib.Path(dsl_nc))
    if active_tab:
        if active_tab == "diff":
            return diff_plots(reference, candidate)
        elif active_tab == "ref":
            return ref_plots(reference, candidate)
        elif active_tab == "dsl":
            return dsl_plots(reference, candidate)
    return []


def spin(arg_reference_nc: str, arg_dsl_nc: str):
    global reference_nc
    reference_nc = arg_reference_nc
    global dsl_nc
    dsl_nc = arg_dsl_nc
    app.run(jupyter_mode="jupyterlab")


if __name__ == "__main__":
    import sys

    spin(sys.argv[1], sys.argv[2])
