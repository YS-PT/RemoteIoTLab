import paho.mqtt.client as mqtt
import json
from datetime import datetime
from app.data_store import add_sensor_data

# MQTT configuration
MQTT_BROKER = 'fa8abb9aa92b4c85bb9540320242427f.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'fyp/RemoteIoT'
MQTT_USER = 'ESP32S3-1'
MQTT_PASSWORD = 'HiveMQ11'


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        print("Received raw MQTT message:", payload)

        # Parse the JSON payload
        data = json.loads(payload)

        # Add the formatted data to the store
        formatted_data = {
            'timestamp': data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'temp_dht11': data.get('DHT11_Temperature', 0),
            'hum_dht11': data.get('DHT11_Humidity', 0),
            'temp_ds18b20': data.get('DS18B20_Temperature', 0),
            'light_intensity': data.get('Light_Intensity', 0)
        }
        add_sensor_data(formatted_data)
    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
