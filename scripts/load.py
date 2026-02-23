import psycopg2
import os
from dotenv import load_dotenv
import sys
from elasticsearch import Elasticsearch
import urllib3
from datetime import datetime, timezone


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

sys.path.append(os.path.dirname(__file__))

from extract import extract_weather
from transform import transform_weather

# Postgres config
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

ES_PASSWORD = os.getenv("ELASTIC_PASSWORD")

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", ES_PASSWORD),
    verify_certs=False
)


def load_to_postgres(dim_city, dim_time, fact_weather):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    cur = conn.cursor()

    for _, row in dim_city.iterrows():
        cur.execute("""
            INSERT INTO dim_city (city_id, city, lat, lon)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (city_id) DO NOTHING
        """, (
            int(row["city_id"]),
            str(row["city"]),
            float(row["lat"]),
            float(row["lon"])
        ))

    for _, row in dim_time.iterrows():
        cur.execute("""
            INSERT INTO dim_time (time_id, timestamp, hour, day, month, year)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (time_id) DO NOTHING
        """, (
            int(row["time_id"]),
            row["timestamp"],
            int(row["hour"]),
            int(row["day"]),
            int(row["month"]),
            int(row["year"])
        ))

    for _, row in fact_weather.iterrows():
        cur.execute("""
            INSERT INTO fact_weather (
                city_id, time_id,
                temperature, temperature_f,
                humidity, pressure, wind_speed, visibility
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(row["city_id"]),
            int(row["time_id"]),
            float(row["temperature"]),
            float(row["temperature_f"]),
            int(row["humidity"]),
            int(row["pressure"]),
            float(row["wind_speed"]),
            int(row["visibility"]) if row["visibility"] else None
        ))

    conn.commit()
    cur.close()
    conn.close()


def load_to_elasticsearch(data):
    for item in data:
        doc = {
            "city": item["name"],
            "temperature": float(item["main"]["temp"]),
            "humidity": int(item["main"]["humidity"]),
            "pressure": int(item["main"]["pressure"]),
            "wind_speed": float(item["wind"]["speed"]),
            "timestamp": datetime.fromtimestamp(item["dt"], timezone.utc).isoformat(),
            "location": {
                "lat": float(item["coord"]["lat"]),
                "lon": float(item["coord"]["lon"])
            }
        }

        es.index(index="weather", document=doc)


if __name__ == "__main__":
    data = extract_weather()

    dim_city, dim_time, fact_weather = transform_weather(data)

    load_to_postgres(dim_city, dim_time, fact_weather)
    load_to_elasticsearch(data)
