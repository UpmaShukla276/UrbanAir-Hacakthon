"""
WAQI Ground-Truth AQI Collector
==================================
Fetches ground-station AQI (via aqicn.org's WAQI network) for all 21
Delhi-NCR points.

NOTE: WAQI's feed/geo:{lat};{lon} endpoint was found to be broken/
unreachable at the time of writing (returns {"status":"nope","data":
"can not connect"} even with a valid, confirmed token) -- confirmed by
testing feed/<cityname> and map/bounds + feed/@uid, both of which work
fine with the same token. So this collector uses:
  1. map/bounds/  -- returns every real WAQI station inside a lat/lon
     box, purely by geography (no name matching, no dependency on the
     broken geo endpoint).
  2. feed/@{uid}/ -- fetches the actual current AQI for a specific
     station once we know its uid.

For each of the 21 points, we search a box around it, sort the
candidate stations by real distance, and try them nearest-first until
one returns a usable numeric AQI (map/bounds itself often reports "-"
for the aqi field even on stations that DO have current data -- the
individual feed/@uid call is what actually confirms it).

Usage:
    python waqi_aqi_collector.py                 # single fetch, all 21 points
    python waqi_aqi_collector.py --loop 30        # every 30 min, forever
"""

import os
import csv
import sys
import time
import argparse
import requests
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

API_TOKEN = os.environ.get("WAQI_API_TOKEN", "")
BOUNDS_URL = "https://api.waqi.info/map/bounds/"
FEED_BY_UID_URL = "https://api.waqi.info/feed/@{uid}/"

AQI_MODEL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AQI_MODEL_DIR.parent / "urbanair_backend"
LOG_FILE = str(BACKEND_DIR / "live_ground_aqi_log.csv")

MAX_MATCH_DISTANCE_KM = 12.0
BOX_DEGREES = 0.15   # ~15km half-width box around each point to search for stations
MAX_CANDIDATES_TO_TRY = 6  # how many nearest stations to test before giving up


# Only Gurgaon gets a wider radius -- every other point still uses the
# 12km/0.15deg defaults above, untouched.
POINT_MAX_DISTANCE_OVERRIDE = {"Gurgaon": 20.0}



ALL_POINTS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Anand Vihar": (28.6469, 77.3152),
    "Ashok Vihar": (28.6980, 77.1730),
    "Bawana": (28.7996, 77.0339),
    "Dwarka": (28.5730, 77.0410),
    "Jahangirpuri": (28.7280, 77.1636),
    "Mundka": (28.6828, 76.9821),
    "Narela": (28.8553, 77.0888),
    "Okhla": (28.5355, 77.2910),
    "Punjabi Bagh": (28.6692, 77.1341),
    "R.K. Puram": (28.5641, 77.1765),
    "Rohini": (28.7495, 77.0565),
    "Vivek Vihar": (28.6720, 77.3152),
    "Wazirpur": (28.7041, 77.1663),
    "Chandni Chowk": (28.6506, 77.2303),
    "Red Fort": (28.6562, 77.2410),
    "Connaught Place": (28.6315, 77.2167),
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def categorize(aqi):
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


FIELDNAMES = [
    "timestamp", "location_name", "location_lat", "location_lon",
    "aqi", "aqi_category", "station_name", "station_lat", "station_lon",
    "distance_km", "is_directly_measured",
]


def find_stations_in_box(point_lat, point_lon, box_degrees):
    """Returns raw station list from map/bounds for a box around the point.
    Each item looks like {"lat":.., "lon":.., "uid":.., "aqi":"-", "station":{"name":..}}."""
    lat1, lat2 = point_lat - box_degrees, point_lat + box_degrees
    lon1, lon2 = point_lon - box_degrees, point_lon + box_degrees
    resp = requests.get(
        BOUNDS_URL,
        params={"token": API_TOKEN, "latlng": f"{lat1},{lon1},{lat2},{lon2}"},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        return []
    return payload.get("data", [])


def fetch_by_uid(uid):
    resp = requests.get(FEED_BY_UID_URL.format(uid=uid), params={"token": API_TOKEN}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        return None
    return payload["data"]


def find_nearest_verified_station(point_lat, point_lon, point_name=None):
    """Finds every WAQI station near this point, sorts by real distance,
    then tries them nearest-first via feed/@uid until one works. Gurgaon
    uses a wider radius (POINT_MAX_DISTANCE_OVERRIDE) -- every other
    point still uses the 12km/0.15deg defaults, unchanged."""
    max_dist = POINT_MAX_DISTANCE_OVERRIDE.get(point_name, MAX_MATCH_DISTANCE_KM)
    box_degrees = max(BOX_DEGREES, max_dist / 100.0)

    stations = find_stations_in_box(point_lat, point_lon, box_degrees)

    candidates = []
    for s in stations:
        try:
            slat, slon = float(s["lat"]), float(s["lon"])
            uid = s["uid"]
        except (KeyError, TypeError, ValueError):
            continue
        dist = haversine_km(point_lat, point_lon, slat, slon)
        if dist <= max_dist:
            candidates.append((dist, uid, s.get("station", {}).get("name", "")))
    candidates.sort(key=lambda c: c[0])

    for dist, uid, fallback_name in candidates[:MAX_CANDIDATES_TO_TRY]:
        data = fetch_by_uid(uid)
        time.sleep(0.2)
        if data is None:
            continue
        aqi_val = data.get("aqi")
        if isinstance(aqi_val, (int, float)):
            return {
                "aqi": aqi_val,
                "station_name": data.get("city", {}).get("name", fallback_name),
                "distance_km": round(dist, 2),
            }
    return None


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

        for point, (point_lat, point_lon) in ALL_POINTS.items():
            try:
                match = find_nearest_verified_station(point_lat, point_lon, point)
                if match is None:
                    print(f"  [warn] {point}: no verified station within {MAX_MATCH_DISTANCE_KM} km -- skipped, not faked")
                    continue

                is_directly_measured = match["distance_km"] <= 2.0

                writer.writerow({
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "location_name": point,
                    "location_lat": point_lat,
                    "location_lon": point_lon,
                    "aqi": match["aqi"],
                    "aqi_category": categorize(match["aqi"]),
                    "station_name": match["station_name"],
                    "station_lat": point_lat,
                    "station_lon": point_lon,
                    "distance_km": match["distance_km"],
                    "is_directly_measured": is_directly_measured,
                })
                rows_written += 1
                tag = "measured" if is_directly_measured else f"nearest, {match['distance_km']}km away"
                print(f"  [ok] {point} -> AQI {match['aqi']} ({tag}: {match['station_name']})")
            except Exception as e:
                print(f"  [warn] {point} failed: {e}")
            time.sleep(0.3)

    print(f"[{now.isoformat()}] Logged {rows_written}/{len(ALL_POINTS)} points -> {LOG_FILE}")


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