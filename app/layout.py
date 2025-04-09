from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime


def create_layout() -> object:
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

        dbc.Row([
            dbc.Col([
                html.H4("Clear Data"),
                dbc.Button("Clear Data", id="clear-data-button", color="danger", className="my-2"),
                html.Div(id="clear-data-status", className="text-danger")
            ], width=4),

            dbc.Col([
                html.H4("Clear Specific Year Data"),
                dbc.Input(id="year-input", placeholder="Enter year (e.g., 2023)", type="number", min=2000,
                          max=datetime.now().year),
                dbc.Button("Clear Year", id="clear-year-button", color="danger", className="my-2"),
                html.Div(id="clear-year-status", className="text-danger")
            ], width=4),
        ]),

        html.Hr(),

        # MicroPython file upload
        html.H3("Upload MicroPython Code to ESP32S3", className="text-center my-4"),

        dcc.Upload(
            id='upload-code',
            children=html.Div(['Drag and Drop or ', html.A('Select a Python File')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px'
            },
            multiple=False
        ),

        dbc.Button("Send to ESP32S3", id="send-code-button", color="primary", className="my-2"),
        html.Div(id="upload-status", className="text-info"),

        html.Hr(),

        html.H3("ESP32S3 Debug Output", className="text-center my-4"),
        html.Div(id="debug-output", className="text-monospace"),

        dcc.Interval(id='update-interval', interval=2000, n_intervals=0)
    ])
