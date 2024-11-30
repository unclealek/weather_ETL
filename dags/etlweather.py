from airflow import DAG
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import task
from airflow.utils.dates import days_ago
from airflow.sensors.python import PythonSensor
from airflow.datasets import Dataset
import requests
import json
from datetime import datetime

# Latitude and longitude for the desired location (Kuopio, Finland in this case)
LATITUDE = '62.8966'
LONGITUDE = '27.6786'
POSTGRES_CONN_ID = 'postgres_default'
API_CONN_ID = 'open_meteo_api'
TEMP_THRESHOLD = 1.0  # Temperature change threshold in Celsius

weather_dataset = Dataset('weather_data')

def get_current_weather():
    """Get current weather data from API."""
    http_hook = HttpHook(method='GET', http_conn_id=API_CONN_ID)
    url = f'/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true'
    response = http_hook.run(url)
    if response.status_code == 200:
        return response.json()['current_weather']
    raise Exception(f"Failed to fetch weather data: {response.status_code}")

def check_temperature_change():
    """Check if temperature has changed significantly."""
    try:
        # Get current temperature
        current_weather = get_current_weather()
        current_temp = current_weather['temperature']

        # Get last recorded temperature from database
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        last_temp_query = """
            SELECT temperature
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 1;
        """
        result = pg_hook.get_first(last_temp_query)
        
        # If no previous records exist, return True to start recording
        if result is None:
            print("No previous temperature records found. Starting to record.")
            return True
            
        last_temp = result[0]

        # Check if temperature change exceeds threshold
        temp_change = abs(current_temp - last_temp)
        print(f"Current temp: {current_temp}°C, Last temp: {last_temp}°C, Change: {temp_change}°C")
        return temp_change >= TEMP_THRESHOLD
    except Exception as e:
        print(f"Error checking temperature change: {e}")
        return False

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1)
}

# DAG
with DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    schedule='@hourly',  # Check every hour
    catchup=False
) as dag:

    # Sensor to check temperature changes
    check_temp = PythonSensor(
        task_id='check_temperature_change',
        python_callable=check_temperature_change,
        mode='poke',
        poke_interval=300,  # Check every 5 minutes
        timeout=3600,  # Timeout after 1 hour
        outlets=[weather_dataset]
    )

    @task()
    def extract_weather_data():
        """Extract weather data from Open-Meteo API using Airflow Connection."""
        try:
            current_weather = get_current_weather()
            print(f"Extracted weather data: {current_weather}")
            return current_weather
        except Exception as e:
            print(f"Error extracting weather data: {e}")
            raise

    @task()
    def transform_weather_data(weather_data):
        """Transform the extracted weather data."""
        transformed_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'temperature': weather_data['temperature'],
            'windspeed': weather_data['windspeed'],
            'winddirection': weather_data['winddirection'],
            'weathercode': weather_data['weathercode']
        }
        print(f"Transformed data: {transformed_data}")
        return transformed_data

    @task()
    def load_weather_data(transformed_data):
        """Load transformed data into PostgreSQL."""
        # Create a PostgreSQL Hook
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        try:
            # Create table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS weather_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                temperature FLOAT NOT NULL,
                windspeed FLOAT NOT NULL,
                winddirection FLOAT NOT NULL,
                weathercode INTEGER NOT NULL
            );
            """
            cursor.execute(create_table_sql)

            # Insert the new weather data
            insert_sql = """
            INSERT INTO weather_data (timestamp, temperature, windspeed, winddirection, weathercode)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_sql, (
                transformed_data['timestamp'],
                transformed_data['temperature'],
                transformed_data['windspeed'],
                transformed_data['winddirection'],
                transformed_data['weathercode']
            ))

            print(f"Successfully inserted weather data: {transformed_data}")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error loading weather data: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # DAG Workflow - ETL Pipeline with proper task dependencies
    weather_data = extract_weather_data()
    transformed_data = transform_weather_data(weather_data)
    check_temp >> weather_data >> transformed_data >> load_weather_data(transformed_data)