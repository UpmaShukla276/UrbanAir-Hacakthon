

import os
import csv
import sys
import time
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # reads .env file in the current directory, if present

API_TOKEN = os.environ.get("WAQI_API_TOKEN", "")
BASE_URL = "https://api.waqi.info/feed/geo:{lat};{lon}/"

LOG_FILE = "live_ground_aqi_log.csv"

CITY_COORDS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}


def categorize(aqi):
    """Same CPCB bands used everywhere else in the app (AQI_CATEGORY_COLORS
    in main.py, SEVERITY_ORDER in AqiGauge.jsx)."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Satisfactory"
    elif aqi <= 200:
        return "Moderate"
    elif aqi <= 300:
        return "Poor"
    elif aqi <= 400:
        return "Very Poor"
    else:
        return "Severe"


FIELDNAMES = ["timestamp", "location_name", "location_lat", "location_lon", "aqi", "aqi_category", "station_name"]


def fetch_city(lat, lon):
    resp = requests.get(BASE_URL.format(lat=lat, lon=lon), params={"token": API_TOKEN}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(payload.get("data", "unknown error"))
    return payload["data"]


def run_once():
    if not API_TOKEN:
        print("ERROR: set WAQI_API_TOKEN environment variable first (or put it in .env).")
        sys.exit(1)

    file_exists = os.path.exists(LOG_FILE)
    now = datetime.now()

    rows_written = 0
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for city, (lat, lon) in CITY_COORDS.items():
            try:
                data = fetch_city(lat, lon)
                aqi_val = data.get("aqi")
                if not isinstance(aqi_val, (int, float)):
                    print(f"  [warn] {city}: no numeric AQI in response, skipping")
                    continue
                writer.writerow({
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "location_name": city,
                    "location_lat": lat,
                    "location_lon": lon,
                    "aqi": aqi_val,
                    "aqi_category": categorize(aqi_val),
                    "station_name": data.get("city", {}).get("name", ""),
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
