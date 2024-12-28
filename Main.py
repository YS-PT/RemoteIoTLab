import streamlit as st
import pandas as pd
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT settings
mqtt_server = 'fa8abb9aa92b4c85bb9540320242427f.s1.eu.hivemq.cloud'  # Replace with your HiveMQ broker URL
mqtt_port = 8883  # Default MQTT port
mqtt_user = 'e0939484@u.nus.edu'  # Replace with your HiveMQ username
mqtt_password = '666666Syy'  # Replace with your HiveMQ password
topic = 'home/temperature'

# Initialize data storage
if 'data' not in st.session_state:
    st.session_state.data = []


# Callback function to handle incoming MQTT messages
def on_message(client, userdata, message):
    msg = message.payload.decode()
    temperature = float(msg.split(':')[1].strip().strip('}'))
    timestamp = datetime.now()
    st.session_state.data.append({'timestamp': timestamp, 'temperature': temperature})


# Connect to MQTT broker and subscribe to topic
def connect_mqtt():
    client = mqtt.Client()
    client.username_pw_set(mqtt_user, mqtt_password)
    client.on_message = on_message
    client.connect(mqtt_server, mqtt_port, 60)
    client.subscribe(topic)
    client.loop_start()
    return client


# Start the MQTT client
client = connect_mqtt()

st.title('IoT Data Dashboard')

# Sidebar for time of day filtering
st.sidebar.header('Filter by Time of Day')
time_of_day = st.sidebar.selectbox('Select Time of Day:', ['All', 'Morning', 'Afternoon', 'Evening', 'Night'])


# Filter the data based on the selected time of day
def filter_data(df, time_of_day):
    if time_of_day == 'Morning':
        df = df[df['timestamp'].dt.hour.between(6, 12)]
    elif time_of_day == 'Afternoon':
        df = df[df['timestamp'].dt.hour.between(12, 18)]
    elif time_of_day == 'Evening':
        df = df[df['timestamp'].dt.hour.between(18, 21)]
    elif time_of_day == 'Night':
        df = df[(df['timestamp'].dt.hour >= 21) | (df['timestamp'].dt.hour < 6)]
    return df


# Display data
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = filter_data(df, time_of_day)

    st.write('Filtered IoT data:')
    st.write(df)

    # Plotting temperature values
    st.line_chart(df.set_index('timestamp')['temperature'])

# Add a button to manually refresh data
if st.button('Refresh Data'):
    st.rerun()