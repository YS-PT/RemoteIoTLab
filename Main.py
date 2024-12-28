import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Initialize data storage
data = []


# Function to receive data
def receive_data():
    global data
    url = 'https://share.streamlit.io/user/ys-pt/remoteiotlab-udvhdlzcv9b6cygrqx6mt7'  # This should be the public URL when deployed
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        received_data = response.json()
        temp = received_data.get('temperature')
        timestamp = datetime.now()
        data.append({'timestamp': timestamp, 'temperature': temp})
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
    except ValueError as e:
        st.error(f"JSON decode error: {e}")


# Streamlit dashboard
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


# Receive data
receive_data()

# Display data
if data:
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = filter_data(df, time_of_day)

    st.write('Filtered IoT data:')
    st.write(df)

    # Plotting temperature values
    st.line_chart(df.set_index('timestamp')['temperature'])

# Add a button to manually refresh data
if st.button('Refresh Data'):
    # Use query params to trigger a re-run
    st.query_params(refresh_data=datetime.now().isoformat())