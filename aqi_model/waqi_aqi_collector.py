"""
WAQI Ground-Truth AQI Collector
==================================
Fetches ground-station AQI (via aqicn.org's WAQI network) for all 21
Delhi-NCR points, with DISTANCE VERIFICATION applied uniformly to
every point (including the 5 "trained" cities) -- a name match alone
isn't trusted; the returned station's own coordinates must be within
MAX_MATCH_DISTANCE_KM of this point's known location, or the point is
logged as "no station" rather than silently substituting a wrong one.

IMPORTANT CAVEAT (surface this in the UI, don't hide it):
WAQI's headline "aqi" figure is computed by WAQI's own real-time index
formula from raw pollutant concentrations. For many stations this
matches India's CPCB scale, but WAQI does not guarantee every station
uses CPCB breakpoints specifically (vs. US EPA breakpoints) -- treat
this as "ground-station-derived AQI via aqicn.org", not an official
CPCB certification, and label it as such in the frontend.

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

load_dotenv()

API_TOKEN = os.environ.get("WAQI_API_TOKEN", "")
SEARCH_URL = "https://api.waqi.info/search/"
FEED_BY_UID_URL = "https://api.waqi.info/feed/@{uid}/"

LOG_FILE = r"D:\urbanair_full_stack\urbanair_full_stack\urbanair_backend\live_ground_aqi_log.csv"

MAX_MATCH_DISTANCE_KM = 12.0

# ALL 21 points, verified the SAME way -- no special-cased "trusted" cities
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

# Search keyword per point -- plain city names search fine as keywords too
SEARCH_KEYWORD = {name: name for name in ALL_POINTS}


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


def find_nearest_verified_station(keyword, point_lat, point_lon):
    """Searches WAQI for this keyword, then picks whichever candidate
    station is physically closest to the point's known coordinates.
    Rejects the match entirely if even the closest one is too far --
    a name match is never trusted on its own."""
    resp = requests.get(SEARCH_URL, params={"token": API_TOKEN, "keyword": keyword}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok" or not payload.get("data"):
        return None

    best, best_dist = None, None
    for s in payload["data"]:
        geo = s.get("station", {}).get("geo")
        if not geo or len(geo) != 2:
            continue
        dist = haversine_km(point_lat, point_lon, geo[0], geo[1])
        if best_dist is None or dist < best_dist:
            best, best_dist = s, dist

    if best is None or best_dist > MAX_MATCH_DISTANCE_KM:
        return None

    return {
        "uid": best["uid"],
        "station_name": best["station"]["name"],
        "station_lat": best["station"]["geo"][0],
        "station_lon": best["station"]["geo"][1],
        "distance_km": round(best_dist, 2),
    }


def fetch_by_uid(uid):
    resp = requests.get(FEED_BY_UID_URL.format(uid=uid), params={"token": API_TOKEN}, timeout=15)
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

        for point, (point_lat, point_lon) in ALL_POINTS.items():
            try:
                match = find_nearest_verified_station(SEARCH_KEYWORD[point], point_lat, point_lon)
                if match is None:
                    print(f"  [warn] {point}: no verified station within {MAX_MATCH_DISTANCE_KM} km -- skipped, not faked")
                    continue

                data = fetch_by_uid(match["uid"])
                aqi_val = data.get("aqi")
                if not isinstance(aqi_val, (int, float)):
                    print(f"  [warn] {point}: matched station has no numeric AQI, skipping")
                    continue

                is_directly_measured = match["distance_km"] <= 2.0  # station essentially AT the point

                writer.writerow({
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "location_name": point,
                    "location_lat": point_lat,
                    "location_lon": point_lon,
                    "aqi": aqi_val,
                    "aqi_category": categorize(aqi_val),
                    "station_name": match["station_name"],
                    "station_lat": match["station_lat"],
                    "station_lon": match["station_lon"],
                    "distance_km": match["distance_km"],
                    "is_directly_measured": is_directly_measured,
                })
                rows_written += 1
                tag = "measured" if is_directly_measured else f"nearest, {match['distance_km']}km away"
                print(f"  [ok] {point} -> AQI {aqi_val} ({tag}: {match['station_name']})")
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