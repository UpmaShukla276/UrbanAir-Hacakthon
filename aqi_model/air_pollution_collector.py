

import os
import csv
import sys
import time
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # reads .env file in the current directory, if present

API_KEY = os.environ.get("OWM_API_KEY", "")
AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"

CITY_COORDS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}

LOG_FILE = "live_pollutants_log.csv"

FIELDNAMES = [
    "timestamp", "location_name", "location_lat", "location_lon",
    "co", "no2", "o3", "pm10", "pm25", "so2",
    "owm_aqi_index",  # OWM's own 1-5 index, kept for reference only -- NOT the CPCB AQI
]


def fetch_pollution(lat, lon):
    params = {"lat": lat, "lon": lon, "appid": API_KEY}
    resp = requests.get(AIR_POLLUTION_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()["list"][0]  # current reading is always list[0]


def run_once():
    if not API_KEY:
        print("ERROR: set OWM_API_KEY environment variable first (or put it in .env).")
        sys.exit(1)

    file_exists = os.path.exists(LOG_FILE)
    now = datetime.now()  # local time, matches how the rest of the dashboard displays "now"

    rows_written = 0
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for city, (lat, lon) in CITY_COORDS.items():
            try:
                d = fetch_pollution(lat, lon)
                comp = d["components"]
                writer.writerow({
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "location_name": city,
                    "location_lat": lat,
                    "location_lon": lon,
                    "co": round(comp["co"] / 1000, 4),  # ug/m3 -> mg/m3, see unit note above
                    "no2": comp["no2"],
                    "o3": comp["o3"],
                    "pm10": comp["pm10"],
                    "pm25": comp["pm2_5"],
                    "so2": comp["so2"],
                    "owm_aqi_index": d["main"]["aqi"],
                })
                rows_written += 1
            except Exception as e:
                print(f"  [warn] {city} failed: {e}")
            time.sleep(0.3)  # be nice to the free-tier rate limit

    print(f"[{now.isoformat()}] Logged {rows_written}/{len(CITY_COORDS)} cities -> {LOG_FILE}")


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
