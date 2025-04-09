import paho.mqtt.client as mqtt
import json
from datetime import datetime
from app.data_store import add_sensor_data

# MQTT configuration
MQTT_BROKER = 'fa8abb9aa92b4c85bb9540320242427f.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'fyp/RemoteIoT'
MQTT_TOPIC_CODE = 'ESP32/Code_Upload'
MQTT_TOPIC_DEBUG = 'ESP32/Debug'
MQTT_USER = 'ESP32S3-1'
MQTT_PASSWORD = 'HiveMQ11'

#MQTT Client Initialization
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set()  # Enable TLS for secure connection


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC_DEBUG)
    client.subscribe(MQTT_TOPIC_CODE)  # Subscribe to OTA updates


def on_message(client, userdata, msg):
    """ Handles incoming MQTT messages """
    try:
        payload = msg.payload.decode('utf-8')
        print(f"Received MQTT message on {msg.topic}: {payload}")

        if msg.topic == MQTT_TOPIC:
            process_sensor_data(payload)
        elif msg.topic == MQTT_TOPIC_DEBUG:
            process_debug_message(payload)
        elif msg.topic == MQTT_TOPIC_CODE:
            send_code_to_esp32(payload)  # Handle OTA update
    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def process_sensor_data(payload):
    """ Parses and stores sensor data """
    try:
        data = json.loads(payload)
        formatted_data = {
            'timestamp': data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'temp_dht11': data.get('DHT11_Temperature', 0),
            'hum_dht11': data.get('DHT11_Humidity', 0),
            'temp_ds18b20': data.get('DS18B20_Temperature', 0),
            'light_intensity': data.get('Light_Intensity', 0)
        }
        add_sensor_data(formatted_data)
    except Exception as e:
        print(f"Error processing sensor data: {e}")


def process_debug_message(payload):
    """ Handles debug messages from ESP32 """
    print(f"ESP32 Debug Output: {payload}")


def send_code_to_esp32(filename, code_string):
    try:
        new_client = mqtt.Client()
        new_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        new_client.tls_set()
        new_client.connect(MQTT_BROKER, MQTT_PORT, 60)

        payload = {
            "filename": filename,        # e.g. "student_script.py"
            "code": code_string          # full code text
        }

        new_client.publish("fyp/code_update", json.dumps(payload))
        new_client.disconnect()
        print("✅ Code sent to ESP32S3")
    except Exception as e:
        print("MQTT OTA Send Error:", e)


def start_mqtt():
    """ Starts the MQTT loop """
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
