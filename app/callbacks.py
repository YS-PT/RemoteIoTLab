import pandas as pd
import io
import json
from dash import dcc, callback_context, exceptions
from dash.dependencies import Input, Output, State
from plotly.graph_objs import Scatter, Figure
from app.data_store import get_sensor_data
from app.data_store import clear_in_memory_data, clear_database, clear_year_data


def register_callbacks(app):
    @app.callback(
        [
            Output('dht11-temp-chart', 'figure'),
            Output('dht11-humidity-chart', 'figure'),
            Output('ds18b20-temp-chart', 'figure'),
            Output('light-intensity-chart', 'figure')
        ],
        Input('update-interval', 'n_intervals')
    )
    def update_charts(n):
        # Fetch sensor data
        data = get_sensor_data()

        # Check if data is empty
        if not data:
            empty_fig = Figure()
            empty_fig.update_layout(title="No Data Available", xaxis_title="Time", yaxis_title="Value")
            return empty_fig, empty_fig, empty_fig, empty_fig

        # Extract data for plotting
        timestamps = [entry['timestamp'] for entry in data]
        temp_dht11 = [entry['temp_dht11'] for entry in data]
        hum_dht11 = [entry['hum_dht11'] for entry in data]
        temp_ds18b20 = [entry['temp_ds18b20'] for entry in data]
        light_intensity = [entry['light_intensity'] for entry in data]

        # Create figures with proper error handling
        try:
            temp_fig = Figure()
            temp_fig.add_trace(Scatter(x=timestamps, y=temp_dht11, mode='lines+markers', name='DHT11 Temp (°C)'))
            temp_fig.update_layout(title="DHT11 Temperature", xaxis_title="Time", yaxis_title="Temperature (°C)")

            humidity_fig = Figure()
            humidity_fig.add_trace(Scatter(x=timestamps, y=hum_dht11, mode='lines+markers', name='DHT11 Humidity (%)'))
            humidity_fig.update_layout(title="DHT11 Humidity", xaxis_title="Time", yaxis_title="Humidity (%)")

            ds18b20_fig = Figure()
            ds18b20_fig.add_trace(Scatter(x=timestamps, y=temp_ds18b20, mode='lines+markers', name='DS18B20 Temp (°C)'))
            ds18b20_fig.update_layout(title="DS18B20 Temperature", xaxis_title="Time", yaxis_title="Temperature (°C)")

            light_fig = Figure()
            light_fig.add_trace(Scatter(x=timestamps, y=light_intensity, mode='lines+markers', name='Light Intensity'))
            light_fig.update_layout(title="Light Intensity", xaxis_title="Time", yaxis_title="Intensity")

            return temp_fig, humidity_fig, ds18b20_fig, light_fig

        except Exception as e:
            print(f"Error updating charts: {e}")
            empty_fig = Figure()
            empty_fig.update_layout(title="Error Loading Data", xaxis_title="Time", yaxis_title="Value")
            return empty_fig, empty_fig, empty_fig, empty_fig

    # Download data as CSV or JSON
    @app.callback(
        Output("download-datafile", "data"),
        [Input("download-csv-button", "n_clicks"),
         Input("download-json-button", "n_clicks")],
        prevent_initial_call=True
    )
    def download_data(n_csv, n_json):
        ctx = callback_context
        if not ctx.triggered:
            raise exceptions.PreventUpdate

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        data = get_sensor_data()
        df = pd.DataFrame(data)

        if triggered_id == "download-csv-button":
            # Generate CSV data
            return dcc.send_data_frame(df.to_csv, "sensor_data.csv", index=False)

        elif triggered_id == "download-json-button":
            # Generate JSON data
            json_data = json.dumps(data, indent=2)
            return dcc.send_bytes(json_data.encode(), "sensor_data.json")

    @app.callback(
        Output("clear-data-status", "children"),
        Input("clear-data-button", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_data(n_clicks):
        try:
            # Clear both in-memory data and database
            clear_in_memory_data()
            clear_database()
            return "All data has been cleared successfully!"
        except Exception as e:
            return f"Error clearing data: {e}"

    @app.callback(
        Output("clear-year-status", "children"),
        [Input("clear-year-button", "n_clicks")],
        [State("year-input", "value")],
        prevent_initial_call=True
    )
    def clear_specific_year(n_clicks, year):
        if year is None:
            return "Please enter a valid year."

        result = clear_year_data(year)
        return result
