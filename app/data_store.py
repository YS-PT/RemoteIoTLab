import sqlite3
from datetime import datetime

DB_NAME = 'sensor_data.db'

sensor_data_list = []

DB_PATH = "sensor_data.db"  # Path to your SQLite database file


# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            temp_dht11 REAL,
                            hum_dht11 REAL,
                            temp_ds18b20 REAL,
                            light_intensity REAL
                        )''')
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except sqlite3.DatabaseError as e:
        print(f"Error initializing database: {e}")


# Add sensor data to the database
def add_sensor_data(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO sensor_data 
                          (timestamp, temp_dht11, hum_dht11, temp_ds18b20, light_intensity) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (data['timestamp'], data['temp_dht11'], data['hum_dht11'], data['temp_ds18b20'],
                        data['light_intensity']))
        conn.commit()
        conn.close()
        print("Sensor data added successfully.")
    except sqlite3.DatabaseError as e:
        print(f"Error adding data to database: {e}")


# Retrieve sensor data from the database
def get_sensor_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT timestamp, temp_dht11, hum_dht11, temp_ds18b20, light_intensity FROM sensor_data''')
        rows = cursor.fetchall()
        conn.close()

        # Convert the data into a list of dictionaries
        sensor_data = [
            {
                'timestamp': row[0],
                'temp_dht11': row[1],
                'hum_dht11': row[2],
                'temp_ds18b20': row[3],
                'light_intensity': row[4]
            }
            for row in rows
        ]
        return sensor_data
    except sqlite3.DatabaseError as e:
        print(f"Error retrieving data from database: {e}")
        return []


def add_sensor_data(data):
    global sensor_data_list
    sensor_data_list.append(data)
    # Limit the size of the data list
    if len(sensor_data_list) > 1000:
        sensor_data_list.pop(0)


def get_sensor_data():
    return sensor_data_list


# Call init_db() to ensure the database is set up when the module is imported
init_db()
