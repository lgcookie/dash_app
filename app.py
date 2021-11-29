# Import required libraries
from numpy.core.fromnumeric import var
from controls import VARIABLES
import pickle
import copy
import pathlib
import urllib.request
import plotly.express as px
import dash
import math
import datetime as dt
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
pd.set_option('chained', None)

# Multi-dropdown options


# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[
        {"name": "viewport", "content": "width=device-width"}],
)
app.title = "CRE Forecast"
server = app.server

# Create controls

variables_options = [
    {"label": str(VARIABLES[variables]), "value": str(variables)}
    for variables in VARIABLES
]


# Load data
df = pd.read_excel(
    DATA_PATH.joinpath("sample_data.xlsx"), index_col='Quarter'
)
df.index = pd.to_datetime(df.index)
# df = df[df["Date"] > dt.datetime(1960, 1, 1)]


# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("Bank_of_England.svg.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "CRE Dashboard",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Forecast Overview", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Learn More", id="learn-more-button"),
                            href="https://www.investopedia.com/terms/c/commercialrealestate.asp",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Filter by year (or select range in histogram):",
                            className="control_label",
                        ),
                        dcc.RangeSlider(
                            id="year_slider",
                            min=1987,
                            max=2021,
                            value=[1990, 2018],
                            className="dcc_control",
                        ),
                        html.P(
                            "Plot Time Series:",
                            className="control_label",
                        ),
                        dcc.Checklist(
                            id="variables_selector",
                            options=variables_options,
                            className="dcc_control",
                            value=list(VARIABLES.keys()),
                        ), html.P("Series Transformations:",
                                  className="control_label"),
                        dcc.RadioItems(
                            id="difference_selector",
                            options=[
                                {"label": "Levels", "value": 0},
                                {"label": "1st Diff", "value": 1},
                                {"label": "2nd Diff", "value": 2},
                            ],
                            value=1,
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.P("VAR/VECM Parameters:",
                               className="control_label"),
                        html.P("Number of obs to test",
                               className="control_label"),
                        dcc.Slider(id="num-obs-to-test",
                                   min=0,
                                   max=10,
                                   step=1,
                                   value=5,
                                   tooltip={"placement": "bottom",
                                            "always_visible": True},
                                   ), html.P("Number of obs to predict",
                                             className="control_label"),
                        dcc.Slider(id="num-obs-to-predict",
                                   min=0,
                                   max=16,
                                   step=1,
                                   value=4,
                                   tooltip={"placement": "bottom",
                                            "always_visible": True},
                                   ),

                        html.P("Ignore COVID:",
                               className="control_label"),
                        dcc.RadioItems(
                            id="ignore-covid-selector",
                            options=[
                                {"label": "Yes", "value": 1},
                                {"label": "No ", "value": 0},
                            ],
                            value=1,
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.P("Signifiance level of tests:",
                               className="control_label"),
                        dcc.RadioItems(
                            id="significance-selector",
                            options=[
                                {"label": "0.01", "value": 0.01},
                                {"label": "0.05", "value": 0.05},
                                {"label": "0.1 ", "value": 0.1},
                            ],
                            value=0.01,
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.Button('Run VAR & VECM',
                                    id='submit-val', n_clicks=0),
                        html.Div(id='my-div')
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="well_text"),
                                     html.P("CRE 1 year Growth Rate")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="gasText"), html.P(
                                        "CRE 2 year Growth Rate")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="oilText"), html.P(
                                        "CRE 3 year Growth Rate")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="waterText"), html.P(
                                        "CRE 3 year Growth Rate")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [dcc.Graph(id="count_graph")],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="individual_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions could be useful if employment needs scaled
def human_format(num):
    if num == 0:
        return "0"

    magnitude = int(math.log(num, 1000))
    mantissa = str(int(num / (1000 ** magnitude)))
    return num


@app.callback(
    Output('my-div', 'children'),
    inputs=[Input('submit-val', 'n_clicks')],
    state=[State('num-obs-to-predict', 'value'),
           State('num-obs-to-test', 'value'),
           State('significance-selector', 'value'),
           State('ignore-covid-selector', 'value')]
)
def update_output(n_clicks, num_obs_to_predict, num_obs_to_test, significance_selector, ignore_covid_selector):
    if n_clicks > 0:
        Config = {
            "num_obs_to_predict": num_obs_to_predict,
            "num_obs_to_test": num_obs_to_test,
            "significance_selector": significance_selector,
            "ignore_covid_selector": ignore_covid_selector
        }
        print(n_clicks)
    print(Config)
    return Config


def filter_dataframe(df, variables, year_slider, diff):

    if diff > 0:
        df = df.diff(periods=diff)

    dff = df[[c for c in df.columns if c in variables]]
    dff = dff[
        (dff.index > dt.datetime(year_slider[0], 1, 1))
        & (dff.index < dt.datetime(year_slider[1], 1, 1))
    ]
    print(dff)
    print(variables)
    return dff


# Create callbacks
# app.clientside_callback(
#     ClientsideFunction(namespace="clientside", function_name="resize"),
#     Output("output-clientside", "children"),
#     [Input("count_graph", "figure")],
# )


# @app.callback(
#     Output("aggregate_data", "data"),
#     [
#         Input("variables", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def update_production_text(variables, year_slider):

#     dff = filter_dataframe(df, variables, year_slider)
#     selected = dff["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)
#     return [human_format(sum(gas)), human_format(sum(oil)), human_format(sum(water))]


# Radio -> multi
@app.callback(
    Output("variables", "value"), [Input("variables_selector", "value")]
)
def display_status(selector):

    return list(VARIABLES.keys())


# Slider -> count graph
@app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
def update_year_slider(count_graph_selected):

    if count_graph_selected is None:
        return [1990, 2010]

    nums = [int(point["pointNumber"])
            for point in count_graph_selected["points"]]
    return [min(nums) + 1960, max(nums) + 1961]


# Selectors -> well text
@app.callback(
    Output("well_text", "children"),
    [
        Input("variables", "value"),
        Input("year_slider", "value"),
    ],
)
def update_well_text(variables, year_slider):

    dff = filter_dataframe(df, variables, year_slider)
    return dff.shape[0]


@app.callback(
    [
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
    ],
    [Input("aggregate_data", "data")],
)
def update_text(data):
    return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl"


# Selectors -> main graph
@app.callback(
    Output("count_graph", "figure"),
    [
        Input("variables_selector", "value"),
        Input("year_slider", "value"),
        Input("difference_selector", "value")
    ]
)
def make_main_figure(
    variables, year_slider, diff
):

    dff = filter_dataframe(df, variables, year_slider, diff)
    print(dff)
    dff.loc[:, "Employment"] = dff.loc[:, "Employment"]/10000
    fig = px.line(dff, x=dff.index, y=dff.columns,
                  title='Time Series')
    fig.update_xaxes(
        dtick="M12",
        tickformat="%Y-Q%q", tickangle=45)
    return fig


# Main graph -> individual graph


@app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
def make_individual_figure(main_graph_hover):
    fig = px.line(df, x="Date", y=df.columns,
                  hover_data={"Date": "|%B %d, %Y"},
                  title='custom tick labels')
    fig.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y")
    return fig
# Selectors, main graph -> aggregate graph


@app.callback(
    Output("aggregate_graph", "figure"),
    [
        Input("variables", "value"),
        Input("year_slider", "value"),
        Input("main_graph", "hoverData"),
    ],
)
def make_aggregate_figure(variables, year_slider, main_graph_hover):
    pass
# Selectors, main graph -> pie graph


@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("variables", "value"),
        Input("year_slider", "value"),
    ],
)
def make_pie_figure(variables, year_slider):
    pass


# Selectors -> count graph
# @app.callback(
#     Output("count_graph", "figure"),
#     [
#         Input("variables", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def make_count_figure(variables, year_slider):
#     pass


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
