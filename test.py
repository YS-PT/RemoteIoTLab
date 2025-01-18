import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import paho.mqtt.client as mqtt
import json
import threading
import queue
import time
from datetime import datetime

sensor_data_list = []  # Stores all historical readings
# Dash app initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Global variables to hold sensor data
sensor_data_list = []  # Stores all historical readings
#sensor_data_queue = queue.Queue(maxsize=100)
current_control_command = ""

# MQTT Configuration
MQTT_BROKER = 'fa8abb9aa92b4c85bb9540320242427f.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'fyp/RemoteIoT'
MQTT_USER = 'ESP32S3-1'
MQTT_PASSWORD = 'HiveMQ11'

subscribed = False


def on_connect(client, userdata, flags, rc):
    global subscribed
    print(f"Connected to MQTT Broker with result code {rc}")
    if not subscribed:
        client.subscribe(MQTT_TOPIC, qos=0)
        subscribed = True


# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    global sensor_data_list
    try:
        payload = msg.payload.decode('utf-8')
        print("Received raw MQTT message:", payload)

        # Parse the JSON payload
        data = json.loads(payload)

        # Format the data for dashboard usage
        formatted_data = {
            'timestamp': data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'temp_dht11': data.get('DHT11_Temperature', 0),
            'hum_dht11': data.get('DHT11_Humidity', 0),
            'temp_ds18b20': data.get('DS18B20_Temperature', 0),
            'light_intensity': data.get('Light_Intensity', 0)
        }

        # Add the new data to the list
        sensor_data_list.append(formatted_data)

        # Keep the list size manageable
        if len(sensor_data_list) > 1000:
            sensor_data_list.pop(0)
    except Exception as e:
        print(f"Error processing MQTT message: {e}")


# Start MQTT client in a separate thread
def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# Dash app layout
app.layout = dbc.Container([
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


# Callback to update sensor charts
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
    global sensor_data_list

    # Extract data for plotting
    timestamps = [entry['timestamp'] for entry in sensor_data_list]
    temp_dht11 = [entry['temp_dht11'] for entry in sensor_data_list]
    hum_dht11 = [entry['hum_dht11'] for entry in sensor_data_list]
    temp_ds18b20 = [entry['temp_ds18b20'] for entry in sensor_data_list]
    light_intensity = [entry['light_intensity'] for entry in sensor_data_list]

    # Create individual figures
    temp_fig = go.Figure()
    humidity_fig = go.Figure()
    ds18b20_fig = go.Figure()
    light_fig = go.Figure()

    if timestamps:
        temp_fig.add_trace(go.Scatter(x=timestamps, y=temp_dht11, mode='lines+markers', name='DHT11 Temp (°C)'))
        temp_fig.update_layout(title="DHT11 Temperature", xaxis_title="Time", yaxis_title="Temperature (°C)")

        humidity_fig.add_trace(go.Scatter(x=timestamps, y=hum_dht11, mode='lines+markers', name='DHT11 Humidity (%)'))
        humidity_fig.update_layout(title="DHT11 Humidity", xaxis_title="Time", yaxis_title="Humidity (%)")

        ds18b20_fig.add_trace(go.Scatter(x=timestamps, y=temp_ds18b20, mode='lines+markers', name='DS18B20 Temp (°C)'))
        ds18b20_fig.update_layout(title="DS18B20 Temperature", xaxis_title="Time", yaxis_title="Temperature (°C)")

        light_fig.add_trace(go.Scatter(x=timestamps, y=light_intensity, mode='lines+markers', name='Light Intensity'))
        light_fig.update_layout(title="Light Intensity", xaxis_title="Time", yaxis_title="Intensity")

    return temp_fig, humidity_fig, ds18b20_fig, light_fig


# Callback to send control commands
@app.callback(
    Output("command-status", "children"),
    Input("send-button", "n_clicks"),
    Input("control-input", "value"),
    prevent_initial_call=True
)
def send_command(n_clicks, command):
    global current_control_command
    current_control_command = command

    # Publish command to MQTT
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, json.dumps({"command": command}))
    client.disconnect()

    return f"Command '{command}' sent!"


# Callbacks for downloading data
@app.callback(
    Output("download-datafile", "data"),
    [Input("download-csv-button", "n_clicks"),
     Input("download-json-button", "n_clicks")],
    prevent_initial_call=True
)
def download_data(n_csv, n_json):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Convert data to a DataFrame
    df = pd.DataFrame(sensor_data_list)

    if triggered_id == "download-csv-button":
        # Use dcc.send_data_frame for CSV download
        return dcc.send_data_frame(df.to_csv, "sensor_data.csv", index=False)

    elif triggered_id == "download-json-button":
        # Use a dictionary for JSON download
        return dict(content=json.dumps(sensor_data_list, indent=4), filename="sensor_data.json")


# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, host="192.168.0.240", port=8050)
