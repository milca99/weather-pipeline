import pandas as pd
from datetime import datetime


def transform_weather(data):
    records = []

    for item in data:
        record = {
            "city": item["name"],
            "temperature": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "weather": item["weather"][0]["description"],
            "pressure": item["main"]["pressure"],
            "wind_speed": item["wind"]["speed"],
            "visibility": item.get("visibility", None),
            "timestamp": datetime.fromtimestamp(item["dt"]),
            "temperature_f": item["main"]["temp"] * 9/5 + 32,
            "lat": item["coord"]["lat"],
            "lon": item["coord"]["lon"]
        }

        records.append(record)

    df = pd.DataFrame(records)


    dim_city = df[["city", "lat", "lon"]].drop_duplicates().reset_index(drop=True)
    dim_city["city_id"] = dim_city.index + 1 

    dim_time = df[["timestamp"]].drop_duplicates().reset_index(drop=True)
    dim_time["time_id"] = dim_time.index + 1

    dim_time["hour"] = dim_time["timestamp"].dt.hour
    dim_time["day"] = dim_time["timestamp"].dt.day
    dim_time["month"] = dim_time["timestamp"].dt.month
    dim_time["year"] = dim_time["timestamp"].dt.year


    fact = df.merge(dim_city, on=["city", "lat", "lon"])
    fact = fact.merge(dim_time, on="timestamp")

    fact_weather = fact[[
        "city_id",
        "time_id",
        "temperature",
        "temperature_f",
        "humidity",
        "pressure",
        "wind_speed",
        "visibility"
    ]]

    return dim_city, dim_time, fact_weather