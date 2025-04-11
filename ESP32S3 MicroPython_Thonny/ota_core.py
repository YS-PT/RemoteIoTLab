from machine import Pin, I2C, ADC, SoftI2C, reset
import dht, ds18x20, onewire, network, time, ssl, json, os
from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C
from machine import reset
import machine

# === Configuration ===
WIFI_SSID = "aa"
WIFI_PASSWORD = "12345678"
MQTT_BROKER = 'a' # replace with actual broker address
MQTT_PORT = 8883
MQTT_USER = 'b'  # replace with actual username 
MQTT_PASSWORD = 'c'  #replace with the password paried with the username
CLIENT_ID = "d"  # set your own id
SENSOR_TOPIC = 'fyp/RemoteIoT'
CODE_TOPIC = "fyp/code_update"
DEBUG_TOPIC = "fyp/debug_output"

# SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_NONE

# Global MQTT client
client = None

# === Hardware Setup ===
dht_sensor = dht.DHT11(Pin(21))
ow = onewire.OneWire(Pin(13))
ds_sensor = ds18x20.DS18X20(ow)
roms = ds_sensor.scan()
light_sensor = ADC(Pin(7))
light_sensor.atten(ADC.ATTN_11DB)

i2c = SoftI2C(scl=Pin(21), sda=Pin(47))
oled = SSD1306_I2C(128, 64, i2c)

# === Wi-Fi ===
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("Wi-Fi connected:", wlan.ifconfig())
    
# === MQTT Connect ===
def connect_mqtt():
    global client
    retries = 0
    while retries < 5:
        try:
            client = MQTTClient(client_id=CLIENT_ID, server=MQTT_BROKER, port=MQTT_PORT,
                            user=MQTT_USER, password=MQTT_PASSWORD, ssl=context)

            client.set_callback(receive_code_update)  # ✅ Set callback BEFORE connect
            client.connect(clean_session=True)
            client.subscribe(CODE_TOPIC)      # ✅ Subscribe to code topic
            print(f"✅ Connected to MQTT: {MQTT_BROKER}, subscribed to {CODE_TOPIC}")
            return True
        except Exception as e:
            print(f"⚠️ MQTT connect error ({retries+1}/5): {e}")
            retries += 1
            time.sleep(5)
            machine.deepsleep(5000)
    print("❌ MQTT failed after retries. Rebooting...")
    machine.deepsleep(5000)
        
# === OTA Callback ==
def receive_code_update(topic, msg):
    global client
    print("✅ OTA message received on topic:", topic)
    try:
        code = msg.decode()  # directly decode incoming Python script
        filename = data.get("filename", "user_script.py")
        code = data.get("code", "")
        with open(filename, "w") as f:
            f.write(code)
            f.flush()
        client.publish(DEBUG_TOPIC, f"✅ OTA: Saved {filename}. Running...".encode())
        print(f"🚀 Executing {filename}...")

        # Run the new code immediately without reboot
        exec(code, {"__name__": "__main__"})

        client.publish(DEBUG_TOPIC, f"✅ Execution of {filename} complete.".encode())

    except Exception as e:
        error_msg = f"❌ OTA exec error: {str(e)}"
        print(error_msg)
        client.publish(DEBUG_TOPIC, error_msg.encode())

    
            
# === Read Sensors ===
def read_sensors():
    dht_sensor.measure()
    ds_sensor.convert_temp()
    time.sleep(1)
    return {
        "temp_dht11": dht_sensor.temperature(),
        "hum_dht11": dht_sensor.humidity(),
        "temp_ds18b20": ds_sensor.read_temp(roms[0]),
        "light": light_sensor.read()
    }

# === OLED Display ===
def show_oled(data):
    oled.fill(0)
    oled.text(f"DHT11: {data['temp_dht11']}C", 0, 0)
    oled.text(f"Hum: {data['hum_dht11']}%", 0, 10)
    oled.text(f"DS18B20: {data['temp_ds18b20']}C", 0, 20)
    oled.text(f"Light: {data['light']}", 0, 30)
    oled.text("OTA Active", 0, 50)
    oled.show()

# === MQTT Sensor Publish ===
def publish_data(data):
    timestamp = time.localtime()
    formatted = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d} {timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
    payload = json.dumps({
        "time": formatted,
        "DHT11_Temperature": data['temp_dht11'],
        "DHT11_Humidity": data['hum_dht11'],
        "DS18B20_Temperature": data['temp_ds18b20'],
        "Light_Intensity": data['light']
    })
    client.publish(SENSOR_TOPIC, payload)
    print("Published sensor data:", payload)

# === Run user script on boot ===
def run_saved_script():
    print("🔍 Looking for user-uploaded script to run...")

    for fname in os.listdir():
        print(f"📁 Found file: {fname}")
        if fname.startswith("user") and fname.endswith(".py"):
            try:
                print(f"🚀 Executing: {fname}")
                with open(fname) as f:
                    exec(f.read(), {"__name__": "__main__"})
                client.publish(DEBUG_TOPIC, f"✅ Running user script after reboot".encode())
            except Exception as e:
                client.publish(DEBUG_TOPIC, f"Script error: {str(e)}".encode())
           
# === Main Loop ===
def main():
    global client
    connect_wifi()
    connect_mqtt()
    run_saved_script()

    while True:
        try:
            client.check_msg()  # OTA check
            data = read_sensors()
            show_oled(data)
            publish_data(data)
            for _ in range(10):
                client.check_msg()
                time.sleep(1)
        except OSError as e:
            print(f"⚠️ General error: {e}, reconnecting MQTT...")
            connect_wifi()
            connect_mqtt()




