import streamlit as st
import pandas as pd
from flask import Flask, request
from threading import Thread
import datetime

# Initialize a Flask app
app = Flask(__name__)
data = []


@app.route('/temperature', methods=['POST'])
def temperature():
    global data
    temp = request.json['temperature']
    timestamp = datetime.datetime.now()
    data.append({'timestamp': timestamp, 'temperature': temp})
    return 'OK', 200


def run_flask():
    app.run(host='0.0.0.0', port=8501)


# Start the Flask app in a separate thread
Thread(target=run_flask).start()

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


if data:
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = filter_data(df, time_of_day)

    st.write('Filtered IoT data:')
    st.write(df)

    # Plotting temperature values
    st.line_chart(df.set_index('timestamp')['temperature'])