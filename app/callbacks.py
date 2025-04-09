import pandas as pd
import io
import json
import base64
from dash import dcc, callback_context, exceptions
from dash.dependencies import Input, Output, State
from plotly.graph_objs import Scatter, Figure
from app.data_store import get_sensor_data, clear_in_memory_data, clear_database, clear_year_data
from app.mqtt_client import send_code_to_esp32, client, MQTT_TOPIC_CODE, MQTT_TOPIC_DEBUG


def register_callbacks(app):
    # ------------------------- Sensor Data Update Callback -------------------------
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
        """ Fetches and updates sensor data charts in real time. """
        data = get_sensor_data()

        if not data:
            empty_fig = Figure()
            empty_fig.update_layout(title="No Data Available", xaxis_title="Time", yaxis_title="Value")
            return empty_fig, empty_fig, empty_fig, empty_fig

        timestamps = [entry['timestamp'] for entry in data]
        temp_dht11 = [entry['temp_dht11'] for entry in data]
        hum_dht11 = [entry['hum_dht11'] for entry in data]
        temp_ds18b20 = [entry['temp_ds18b20'] for entry in data]
        light_intensity = [entry['light_intensity'] for entry in data]

        try:
            return (
                Figure(data=[Scatter(x=timestamps, y=temp_dht11, mode='lines+markers', name='DHT11 Temp (°C)')],
                       layout_title_text="DHT11 Temperature"),
                Figure(data=[Scatter(x=timestamps, y=hum_dht11, mode='lines+markers', name='DHT11 Humidity (%)')],
                       layout_title_text="DHT11 Humidity"),
                Figure(data=[Scatter(x=timestamps, y=temp_ds18b20, mode='lines+markers', name='DS18B20 Temp (°C)')],
                       layout_title_text="DS18B20 Temperature"),
                Figure(data=[Scatter(x=timestamps, y=light_intensity, mode='lines+markers', name='Light Intensity')],
                       layout_title_text="Light Intensity"),
            )
        except Exception as e:
            print(f"Error updating charts: {e}")
            empty_fig = Figure()
            empty_fig.update_layout(title="Error Loading Data", xaxis_title="Time", yaxis_title="Value")
            return empty_fig, empty_fig, empty_fig, empty_fig

    # ------------------------- Data Download Callbacks -------------------------
    @app.callback(
        Output("download-datafile", "data"),
        [Input("download-csv-button", "n_clicks"),
         Input("download-json-button", "n_clicks")],
        prevent_initial_call=True
    )
    def download_data(n_csv, n_json):
        """ Allows users to download sensor data as CSV or JSON. """
        ctx = callback_context
        if not ctx.triggered:
            raise exceptions.PreventUpdate

        data = get_sensor_data()
        df = pd.DataFrame(data)
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == "download-csv-button":
            return dcc.send_data_frame(df.to_csv, "sensor_data.csv", index=False)
        elif triggered_id == "download-json-button":
            return dcc.send_bytes(json.dumps(data, indent=2).encode(), "sensor_data.json")

    # ------------------------- Data Clearing Callbacks -------------------------
    @app.callback(
        Output("clear-data-status", "children"),
        Input("clear-data-button", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_data(n_clicks):
        """ Clears all sensor data from memory and database. """
        try:
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
        """ Clears sensor data for a specific year. """
        if year is None:
            return "Please enter a valid year."
        return clear_year_data(year)

    # ------------------------- Code Upload & MQTT OTA Callback -------------------------

    # @app.callback(
    #     Output("upload-status", "children"),
    #     [Input("upload-code", "contents"),
    #      Input("send-code-button", "n_clicks")],
    #     [State("upload-code", "filename")],
    #     prevent_initial_call=True
    # )
    # def handle_upload_and_send(contents, n_clicks, filename):
    #     ctx = callback_context  # Get context to determine trigger
    #
    #     if not ctx.triggered:
    #         return "No action triggered."
    #
    #     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Identify the trigger
    #     """ Handles file upload and sends MicroPython code to ESP32 via MQTT. """
    #     if trigger_id == "upload-code" and contents:
    #         try:
    #             _, content_string = contents.split(',')
    #             decoded = base64.b64decode(content_string).decode('utf-8')
    #
    #             # Send the MicroPython code to ESP32 via MQTT
    #             send_code_to_esp32(decoded)
    #
    #             return f"Successfully uploaded and sent {filename} to ESP32."
    #         except Exception as e:
    #             return f"Error processing file: {e}"
    #
    #     elif trigger_id == "send-code-button" and contents:
    #         try:
    #             _, content_string = contents.split(',')
    #             decoded = base64.b64decode(content_string).decode('utf-8')
    #
    #             # Publish code to ESP32 via MQTT
    #             send_code_to_esp32(decoded)
    #
    #             return "Code sent successfully!"
    #         except Exception as e:
    #             return f"Error: {e}"
    #
    #     return "No valid action performed."

    @app.callback(
        Output("debug-output", "children"),
        [Input("update-interval", "n_intervals")]
    )
    def fetch_debug_output(n):
        """ Fetches real-time debug output from ESP32. """
        debug_logs = []

        def on_message(client, userdata, msg):
            debug_logs.append(msg.payload.decode())

        client.subscribe(MQTT_TOPIC_DEBUG)
        client.on_message = on_message

        return "\n".join(debug_logs) if debug_logs else "Waiting for debug data..."

    @app.callback(
        Output("upload-status", "children"),
        Input("upload-code", "contents"),
        State("upload-code", "filename"),
        prevent_initial_call=True
    )
    def upload_code(contents, filename):
        if not contents:
            return "❌ No file uploaded."

        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string).decode('utf-8')

            # ✅ Pass both filename and decoded code string
            send_code_to_esp32(filename, decoded)

            return f"✅ {filename} sent to ESP32S3 via OTA"
        except Exception as e:
            return f"❌ Error sending code: {e}"

