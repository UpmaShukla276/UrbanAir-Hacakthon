

import os
import csv
import sys
import time
import argparse
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # reads .env file in the current directory, if present

API_KEY = os.environ.get("OWM_API_KEY", "")
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

CITY_CENTERS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}

CURRENT_LOG = "weather_current_log.csv"
FORECAST_LOG = "weather_forecast_log.csv"

CURRENT_FIELDS = [
    "fetch_timestamp", "city", "lat", "lon", "temp", "feels_like", "humidity",
    "pressure", "wind_speed", "wind_deg", "wind_gust", "clouds_pct",
    "visibility", "weather_main", "weather_desc",
]

FORECAST_FIELDS = [
    "fetch_timestamp", "city", "lat", "lon", "forecast_for", "temp", "feels_like",
    "humidity", "pressure", "wind_speed", "wind_deg", "wind_gust", "clouds_pct",
    "pop", "weather_main", "weather_desc",
]


def fetch_current(lat, lon):
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    r = requests.get(CURRENT_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_forecast(lat, lon):
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    r = requests.get(FORECAST_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def run_once():
    if not API_KEY:
        print("ERROR: set OWM_API_KEY environment variable first.")
        sys.exit(1)

    fetch_ts = datetime.now(timezone.utc).isoformat()

    cur_exists = os.path.exists(CURRENT_LOG)
    fc_exists = os.path.exists(FORECAST_LOG)

    with open(CURRENT_LOG, "a", newline="") as cf, open(FORECAST_LOG, "a", newline="") as ff:
        cur_writer = csv.DictWriter(cf, fieldnames=CURRENT_FIELDS)
        fc_writer = csv.DictWriter(ff, fieldnames=FORECAST_FIELDS)
        if not cur_exists:
            cur_writer.writeheader()
        if not fc_exists:
            fc_writer.writeheader()

        for city, (lat, lon) in CITY_CENTERS.items():
            # --- current ---
            try:
                d = fetch_current(lat, lon)
                cur_writer.writerow({
                    "fetch_timestamp": fetch_ts, "city": city, "lat": lat, "lon": lon,
                    "temp": d["main"]["temp"], "feels_like": d["main"]["feels_like"],
                    "humidity": d["main"]["humidity"], "pressure": d["main"]["pressure"],
                    "wind_speed": d["wind"].get("speed"), "wind_deg": d["wind"].get("deg"),
                    "wind_gust": d["wind"].get("gust"), "clouds_pct": d["clouds"]["all"],
                    "visibility": d.get("visibility"),
                    "weather_main": d["weather"][0]["main"], "weather_desc": d["weather"][0]["description"],
                })
            except Exception as e:
                print(f"  [warn] current weather failed for {city}: {e}")

           
            try:
                d = fetch_forecast(lat, lon)
                for item in d.get("list", []):
                    fc_writer.writerow({
                        "fetch_timestamp": fetch_ts, "city": city, "lat": lat, "lon": lon,
                        "forecast_for": item["dt_txt"],
                        "temp": item["main"]["temp"], "feels_like": item["main"]["feels_like"],
                        "humidity": item["main"]["humidity"], "pressure": item["main"]["pressure"],
                        "wind_speed": item["wind"].get("speed"), "wind_deg": item["wind"].get("deg"),
                        "wind_gust": item["wind"].get("gust"), "clouds_pct": item["clouds"]["all"],
                        "pop": item.get("pop"),
                        "weather_main": item["weather"][0]["main"], "weather_desc": item["weather"][0]["description"],
                    })
            except Exception as e:
                print(f"  [warn] forecast failed for {city}: {e}")

            time.sleep(0.3)

    print(f"[{fetch_ts}] Logged current + forecast for {len(CITY_CENTERS)} cities")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", type=int, default=0, help="Minutes between fetches. 0 = run once.")
    args = parser.parse_args()

    if args.loop <= 0:
        run_once()
    else:
        print(f"Looping every {args.loop} min. Ctrl+C to stop.")
        while True:
            run_once()
            time.sleep(args.loop * 60)