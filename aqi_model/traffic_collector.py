

import os
import csv
import sys
import time
import argparse
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # reads .env file in the current directory, if present

API_KEY = os.environ.get("TOMTOM_API_KEY", "")
BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

GRID_FILE = "ncr_grid_points.csv"
LOG_FILE = "traffic_log.csv"

FIELDNAMES = [
    "timestamp", "point_id", "type", "name", "lat", "lon",
    "frc", "current_speed", "free_flow_speed", "current_travel_time",
    "free_flow_travel_time", "confidence", "road_closure",
    "congestion_ratio",  # current_speed / free_flow_speed (lower = more congested)
]


def load_points():
    with open(GRID_FILE) as f:
        return list(csv.DictReader(f))


def fetch_point(lat, lon):
    """Calls TomTom Flow Segment Data API for a single point."""
    params = {"point": f"{lat},{lon}", "key": API_KEY, "unit": "KMPH"}
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()["flowSegmentData"]


def run_once():
    if not API_KEY:
        print("ERROR: set TOMTOM_API_KEY environment variable first.")
        sys.exit(1)

    points = load_points()
    file_exists = os.path.exists(LOG_FILE)
    ts = datetime.now(timezone.utc).isoformat()

    rows_written = 0
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for pt in points:
            try:
                data = fetch_point(pt["lat"], pt["lon"])
                current_speed = data.get("currentSpeed")
                free_flow_speed = data.get("freeFlowSpeed")
                congestion_ratio = (
                    round(current_speed / free_flow_speed, 3)
                    if current_speed and free_flow_speed else None
                )
                writer.writerow({
                    "timestamp": ts,
                    "point_id": pt["point_id"],
                    "type": pt["type"],
                    "name": pt["name"],
                    "lat": pt["lat"],
                    "lon": pt["lon"],
                    "frc": data.get("frc"),
                    "current_speed": current_speed,
                    "free_flow_speed": free_flow_speed,
                    "current_travel_time": data.get("currentTravelTime"),
                    "free_flow_travel_time": data.get("freeFlowTravelTime"),
                    "confidence": data.get("confidence"),
                    "road_closure": data.get("roadClosure"),
                    "congestion_ratio": congestion_ratio,
                })
                rows_written += 1
            except Exception as e:
                print(f"  [warn] {pt['point_id']} failed: {e}")
            time.sleep(0.2)  # be nice to the free-tier rate limit

    print(f"[{ts}] Logged {rows_written}/{len(points)} points -> {LOG_FILE}")


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