import threading
from app import app
from app.data_store import add_sensor_data
from app.layout import create_layout
from app.mqtt_client import start_mqtt
from app.callbacks import register_callbacks
import sys


print("Python Path:", sys.path)
# Set up the layout
app.layout = create_layout()

# Register the callbacks
register_callbacks(app)

if __name__ == '__main__':
    # Start MQTT in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    # Run the Dash app
    app.run_server(debug=True, host="100.118.33.42", port=8050)

