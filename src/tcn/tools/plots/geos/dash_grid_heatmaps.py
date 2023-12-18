import dash_bootstrap_components as dbc  # type: ignore
import xarray as xr  # type: ignore
from dash import Dash, Input, Output, dcc, html  # type: ignore

import tcn.tools.plots.geos.plot_via_plotly as ph

app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

candidate = xr.open_mfdataset(
    "/home/fgdeconi/work/git/smtn/tmp/23.AU.DGPU.DEBUG/dacegpu/state_0009_tile0.nc"
)
reference = xr.open_mfdataset(
    "/home/fgdeconi/work/git/smtn/tmp/23.AU.DGPU.DEBUG/fortran/state_0009_tile0.nc"
)


def diff_plots():
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(
            ph.plot_heatmaps_diff_mean_on_K(candidate, reference, variable=str(c))
        )
    return figs


def ref_plots():
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(ph.plot_heatmaps_mean_on_K(reference, variable=str(c)))
    return figs


def dsl_plots():
    figs = []
    for c in candidate.variables:
        if len(candidate[c].dims) != 5:
            continue
        figs.append(ph.plot_heatmaps_mean_on_K(candidate, variable=str(c)))
    return figs


app.layout = dbc.Container(
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
    if active_tab:
        return dbc.Row([dbc.Col(dcc.Graph(figure=fig), width=6) for fig in data])
    return "No tab selected"


@app.callback(
    Output("store", "data"), [Input("tabs", "active_tab"), Input("button", "n_clicks")]
)
def get_graphs(active_tab, n):
    """
    This callback generates three simple graphs from random data.
    """
    if active_tab:
        if active_tab == "diff":
            return diff_plots()
        elif active_tab == "ref":
            return ref_plots()
        elif active_tab == "dsl":
            return dsl_plots()
    return []


if __name__ == "__main__":
    app.run(debug=True)
