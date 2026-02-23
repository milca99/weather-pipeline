import os
import requests
from dotenv import load_dotenv
from time import sleep

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITIES = [
    "Belgrade",
    "Budapest",
    "Vienna",
    "Sofia",
    "Bucharest",
    "Athens",
    "Skopje",
    "Sarajevo",
    "Podgorica",
    "Ljubljana"
]

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def extract_weather(retries=2, delay=2):
    all_data = []

    for city in CITIES:
        for attempt in range(retries):
            try:
                params = {
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric"
                }

                response = requests.get(BASE_URL, params=params)

                if response.status_code == 200:
                    data = response.json()
                    all_data.append(data)
                    print(f"OK: {city}")
                    break
                else:
                    print(f"Retry {attempt+1} for {city}")
                    sleep(delay)

            except Exception as e:
                print(f"Error for {city}: {e}")
                sleep(delay)

        sleep(1) 

    return all_data


if __name__ == "__main__":
    data = extract_weather()

    print(f"\nFetched {len(data)} records")