from dash import dcc, html
import dash_bootstrap_components as dbc


def create_layout():
    return dbc.Container([
        html.H1("IoT Sensor Dashboard", className="text-center my-4"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='dht11-temp-chart', style={'height': '300px'}),
                dcc.Graph(id='dht11-humidity-chart', style={'height': '300px'}),
            ], width=6),

            dbc.Col([
                dcc.Graph(id='ds18b20-temp-chart', style={'height': '300px'}),
                dcc.Graph(id='light-intensity-chart', style={'height': '300px'}),
            ], width=6),
        ]),

        dbc.Row([
            dbc.Col([
                html.H4("Control Panel"),
                dbc.Input(id="control-input", placeholder="Enter command", type="text"),
                dbc.Button("Send", id="send-button", color="primary", className="my-2"),
                html.Div(id="command-status", className="text-success")
            ], width=4),

            dbc.Col([
                html.H4("Download Data"),
                dbc.Button("Download CSV", id="download-csv-button", color="secondary", className="my-2"),
                dbc.Button("Download JSON", id="download-json-button", color="secondary", className="my-2"),
                dcc.Download(id="download-datafile")
            ], width=4),
        ]),

        dcc.Interval(id='update-interval', interval=2000, n_intervals=0)
    ])
