import json
import math
import time as _time
from pathlib import Path
from datetime import datetime, timezone
 
import pandas as pd
 
BASE_DIR = Path(__file__).resolve().parent
 
CITY_COORDS = {
    # 5 cities with trained nowcast/forecast models
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
 
    # Iconic / high-footfall landmarks (not official DPCC hotspots, but
    # frequently requested for public-facing alerts)
    "Chandni Chowk": (28.6506, 77.2303),
    "Red Fort": (28.6562, 77.2410),
    "Connaught Place": (28.6315, 77.2167),
}
 
# --- Tunable weights (documented assumptions, not fitted) ---
INDUSTRIAL_RADIUS_KM = 5.0
CONSTRUCTION_RADIUS_KM = 2.0   # dust is a short-range effect, unlike industrial smoke
ROAD_BUFFER_KM = 1.5
 
W_TRAFFIC_CONGESTION = 1.0
W_TRAFFIC_ROAD_DENSITY = 0.6
W_INDUSTRIAL = 1.0
W_CONSTRUCTION = 0.8
W_WASTE_BURNING_SEASONAL_BASE = 0.02  # near-zero outside burning season
W_WASTE_BURNING_SEASONAL_PEAK = 3.0   # multiplier during Oct-Nov if wind is from NW
W_BACKGROUND = 1.2
 
 
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
 
 
def bearing_deg(lat1, lon1, lat2, lon2):
    """Bearing FROM point1 TO point2, degrees, 0=North."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360
 
 
def angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)
 
 
def polygon_centroid_and_area(geometry):
    """Rough centroid + area for a GeoJSON polygon/multipolygon (WGS84 degrees,
    approximated as planar -- fine for small NCR-scale distances)."""
    coords_list = []
    if geometry["type"] == "Polygon":
        coords_list = [geometry["coordinates"][0]]
    elif geometry["type"] == "MultiPolygon":
        coords_list = [poly[0] for poly in geometry["coordinates"]]
 
    total_area = 0.0
    cx_sum, cy_sum, weight_sum = 0.0, 0.0, 0.0
    for ring in coords_list:
        if len(ring) < 3:
            continue
        area = 0.0
        cx, cy = 0.0, 0.0
        for i in range(len(ring) - 1):
            x0, y0 = ring[i]
            x1, y1 = ring[i + 1]
            cross = x0 * y1 - x1 * y0
            area += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
        area *= 0.5
        if area == 0:
            continue
        cx /= (6 * area)
        cy /= (6 * area)
        a_abs = abs(area)
        total_area += a_abs
        cx_sum += cx * a_abs
        cy_sum += cy * a_abs
        weight_sum += a_abs
 
    if weight_sum == 0:
        return None, 0.0
    centroid = (cy_sum / weight_sum, cx_sum / weight_sum)  # (lat, lon)
    # Rough km^2: 1 degree lat ~ 111km, 1 degree lon ~ 111km*cos(lat)
    area_km2 = total_area * (111.0 ** 2) * math.cos(math.radians(centroid[0]))
    return centroid, abs(area_km2)
 
 
def load_zone_features(geojson_path):
    with open(geojson_path) as f:
        data = json.load(f)
    zones = []
    for feat in data["features"]:
        centroid, area_km2 = polygon_centroid_and_area(feat["geometry"])
        if centroid and area_km2 > 0:
            zones.append({"lat": centroid[0], "lon": centroid[1], "area_km2": area_km2})
    return zones
 
 
def is_stubble_burning_season(dt):
    """Delhi NCR's dominant waste-burning season: paddy stubble burning in
    Punjab/Haryana, mid-Oct to late-Nov. (Well documented in CPCB/SAFAR
    source-apportionment reports and yearly news coverage.)"""
    return dt.month in (10, 11)
 
 
def compute_source_attribution(point_name, lat, lon, traffic_row, wind_speed, wind_deg,
                                 industrial_zones, construction_zones, road_points_nearby, ref_time):
    # --- Traffic ---
    congestion_ratio = traffic_row["congestion_ratio"] if traffic_row is not None else 1.0
    congestion_component = max(0.0, 1.0 - congestion_ratio)  # 0 = free-flow, ~0.5+ = heavy jam
    road_density_component = min(1.0, road_points_nearby / 50.0)  # normalize against a soft cap
    traffic_raw = W_TRAFFIC_CONGESTION * congestion_component + W_TRAFFIC_ROAD_DENSITY * road_density_component
 
    # --- Industrial (wind-aware: upwind sources contribute more) ---
    industrial_raw = 0.0
    for zone in industrial_zones:
        dist = haversine_km(lat, lon, zone["lat"], zone["lon"])
        if dist > INDUSTRIAL_RADIUS_KM:
            continue
        bearing_source_to_point = bearing_deg(zone["lat"], zone["lon"], lat, lon)
        # wind_deg = direction wind is blowing FROM; pollution travels in the
        # direction wind is blowing TO, i.e. (wind_deg + 180) % 360
        wind_blows_toward = (wind_deg + 180) % 360
        upwind_alignment = max(0.0, 1.0 - angle_diff(wind_blows_toward, bearing_source_to_point) / 90.0)
        calm_factor = 1.0 / (1.0 + wind_speed * 0.15)  # calmer wind -> pollutants stay concentrated
        industrial_raw += (zone["area_km2"] / ((dist + 0.5) ** 2)) * (0.4 + 1.6 * upwind_alignment) * (0.5 + 0.5 * calm_factor)
    industrial_raw *= W_INDUSTRIAL
 
    # --- Construction (short-range dust, wind matters less) ---
    construction_raw = 0.0
    for zone in construction_zones:
        dist = haversine_km(lat, lon, zone["lat"], zone["lon"])
        if dist > CONSTRUCTION_RADIUS_KM:
            continue
        construction_raw += zone["area_km2"] / ((dist + 0.3) ** 2)
    construction_raw *= W_CONSTRUCTION
 
    # --- Waste/stubble burning (seasonal + wind-from-NW heuristic) ---
    seasonal = is_stubble_burning_season(ref_time)
    nw_alignment = max(0.0, 1.0 - angle_diff(wind_deg, 315) / 90.0)  # wind FROM the NW (Punjab/Haryana direction)
    waste_raw = W_WASTE_BURNING_SEASONAL_BASE
    if seasonal:
        waste_raw += W_WASTE_BURNING_SEASONAL_PEAK * nw_alignment * (0.5 + 0.5 / (1.0 + wind_speed * 0.1))
 
    total = traffic_raw + industrial_raw + construction_raw + waste_raw + W_BACKGROUND
    if total == 0:
        total = 1.0  # avoid div by zero; will show equal tiny shares
 
    return {
        "point": point_name,
        "reference_time": ref_time.isoformat(),
        "sources": {
            "traffic_pct": round(100 * traffic_raw / total, 1),
            "industrial_pct": round(100 * industrial_raw / total, 1),
            "construction_pct": round(100 * construction_raw / total, 1),
            "waste_burning_pct": round(100 * waste_raw / total, 1),
            "background_pct": round(100 * W_BACKGROUND / total, 1),
        },
        "raw_signals": {
            "congestion_ratio": round(congestion_ratio, 3),
            "wind_speed_mps": wind_speed,
            "wind_deg": wind_deg,
            "is_stubble_burning_season": seasonal,
        },
    }
 
 
def compute_for_arbitrary_point(lat, lon, traffic_log, weather_log, industrial_zones, construction_zones, road_midpoints, ref_time):
    """Same computation as run_for_all_points(), but for ANY lat/lon --
    not just the 7 pre-registered cities/hotspots. This is what makes the
    tool genuinely 'hyperlocal': source attribution is computed fresh from
    static geospatial layers + nearest live traffic/weather, wherever the
    user clicks or searches."""
    latest_traffic_ts = traffic_log["timestamp"].max()
    latest_traffic = traffic_log[traffic_log["timestamp"] == latest_traffic_ts].copy()
    latest_traffic["dist"] = latest_traffic.apply(lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1)
    traffic_row = latest_traffic.loc[latest_traffic["dist"].idxmin()]
 
    latest_weather_ts = weather_log["fetch_timestamp"].max()
    latest_weather = weather_log[weather_log["fetch_timestamp"] == latest_weather_ts].copy()
    latest_weather["dist"] = latest_weather.apply(lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1)
    weather_row = latest_weather.loc[latest_weather["dist"].idxmin()]
 
    road_count_nearby = sum(
        1 for (rlat, rlon) in road_midpoints if haversine_km(lat, lon, rlat, rlon) <= ROAD_BUFFER_KM
    )
 
    return compute_source_attribution(
        point_name=f"({lat:.4f}, {lon:.4f})", lat=lat, lon=lon,
        traffic_row=traffic_row,
        wind_speed=float(weather_row["wind_speed"]), wind_deg=float(weather_row["wind_deg"]),
        industrial_zones=industrial_zones, construction_zones=construction_zones,
        road_points_nearby=road_count_nearby, ref_time=ref_time,
    )
 
 
_static_layers_cache = None
 
 
def load_static_layers():
    """Loads the static geospatial layers ONCE and caches them in memory --
    these files (roads, industrial, construction zones) never change while
    the server is running, so re-reading/re-parsing them on every single
    request (major_roads.geojson alone has 12,641 features -- 4.2MB) was
    the main reason city switches felt slow. Now: disk read + JSON parse
    happens only on the very first call."""
    global _static_layers_cache
    if _static_layers_cache is not None:
        return _static_layers_cache
 
    industrial_zones = load_zone_features(BASE_DIR / "delhi_ncr_industrial.geojson")
    construction_zones = load_zone_features(BASE_DIR / "delhi_ncr_construction.geojson")
    with open(BASE_DIR / "delhi_ncr_major_roads.geojson") as f:
        roads_data = json.load(f)
    road_midpoints = []
    for feat in roads_data["features"]:
        coords = feat["geometry"]["coordinates"]
        if len(coords) >= 2:
            mid = coords[len(coords) // 2]
            road_midpoints.append((mid[1], mid[0]))
 
    _static_layers_cache = (industrial_zones, construction_zones, road_midpoints)
    return _static_layers_cache
 
 
TRAINED_CITIES = ["Delhi", "Faridabad", "Ghaziabad", "Gurgaon", "Noida"]
 
 
def nearest_known_city(lat, lon):
    """Finds the nearest of the 5 cities with a trained forecast model --
    used to give a proxy AQI/forecast reading for hotspots/landmarks/
    arbitrary locations, since we don't have live pollutant sensors
    everywhere or trained models for every named area."""
    best_city, best_dist = None, float("inf")
    for name in TRAINED_CITIES:
        clat, clon = CITY_COORDS[name]
        d = haversine_km(lat, lon, clat, clon)
        if d < best_dist:
            best_city, best_dist = name, d
    return best_city, best_dist
 
 
def compute_whatif(attribution_result, current_aqi, reductions):
 
    sources = attribution_result["sources"]
    background_pct = sources["background_pct"]
    local_pct_total = 100 - background_pct
 
    background_aqi = current_aqi * (background_pct / 100.0)
    local_aqi = current_aqi * (local_pct_total / 100.0)
 
    new_local_aqi = 0.0
    breakdown = {}
    for key in ["traffic_pct", "industrial_pct", "construction_pct", "waste_burning_pct"]:
        share_of_local = (sources[key] / local_pct_total) if local_pct_total > 0 else 0
        source_aqi_slice = local_aqi * share_of_local
        reduction_frac = reductions.get(key, 0) / 100.0
        new_slice = source_aqi_slice * (1 - reduction_frac)
        new_local_aqi += new_slice
        breakdown[key] = {
            "before_aqi_contribution": round(source_aqi_slice, 1),
            "after_aqi_contribution": round(new_slice, 1),
            "reduction_applied_pct": reductions.get(key, 0),
        }
 
    new_aqi = background_aqi + new_local_aqi
    improvement_pct = round(100 * (current_aqi - new_aqi) / current_aqi, 1) if current_aqi > 0 else 0
 
    return {
        "point": attribution_result["point"],
        "current_aqi": round(current_aqi, 1),
        "simulated_aqi": round(new_aqi, 1),
        "improvement_pct": improvement_pct,
        "background_aqi_floor": round(background_aqi, 1),
        "breakdown": breakdown,
        "disclaimer": "Rough linear-scaling estimate for scenario comparison, not a "
                       "validated atmospheric dispersion model. Population-impact "
                       "estimates require ward-level census data, not yet integrated.",
    }
 
 
_attribution_cache = None
_attribution_cache_time = 0
ATTRIBUTION_CACHE_TTL_SECONDS = 45  # traffic/weather collectors run every few min anyway
 
 
def run_for_all_points():
    """Computes source attribution for all 21 points. Cached for
    ATTRIBUTION_CACHE_TTL_SECONDS -- this loop does 21 points x (up to
    12,641 road midpoints + 635 industrial zones + 251 construction zones)
    of haversine distance math, so without caching, every single call
    (city switch, 60s auto-refresh, enforcement, GRAP, health-advisory)
    was redoing hundreds of thousands of distance calculations from
    scratch. New traffic/weather data only lands every few minutes anyway,
    so a 45s cache doesn't lose any real freshness."""
    global _attribution_cache, _attribution_cache_time
    now = _time.time()
    if _attribution_cache is not None and (now - _attribution_cache_time) < ATTRIBUTION_CACHE_TTL_SECONDS:
        return _attribution_cache
 
    traffic_log = pd.read_csv(BASE_DIR / "traffic_log.csv", parse_dates=["timestamp"])
    weather_log = pd.read_csv(BASE_DIR / "weather_current_log.csv", parse_dates=["fetch_timestamp"])
 
    latest_traffic_ts = traffic_log["timestamp"].max()
    latest_traffic = latest_traffic = traffic_log[traffic_log["timestamp"] == latest_traffic_ts]
 
    latest_weather_ts = weather_log["fetch_timestamp"].max()
    latest_weather = weather_log[weather_log["fetch_timestamp"] == latest_weather_ts]
 
    industrial_zones, construction_zones, road_midpoints = load_static_layers()
 
    ref_time = datetime.now(timezone.utc)
    results = []
 
    for name, (lat, lon) in CITY_COORDS.items():
        traffic_row = None
        matches = latest_traffic[latest_traffic["name"] == name]
        if not matches.empty:
            traffic_row = matches.iloc[0]
        else:
            # fall back to nearest grid point
            latest_traffic = latest_traffic.copy()
            latest_traffic["dist"] = latest_traffic.apply(
                lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1
            )
            traffic_row = latest_traffic.loc[latest_traffic["dist"].idxmin()]
 
        # nearest city's weather (weather is only logged per-city-center)
        weather_row = None
        w_matches = latest_weather[latest_weather["city"] == name]
        if not w_matches.empty:
            weather_row = w_matches.iloc[0]
        else:
            latest_weather = latest_weather.copy()
            latest_weather["dist"] = latest_weather.apply(
                lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1
            )
            weather_row = latest_weather.loc[latest_weather["dist"].idxmin()]
 
        road_count_nearby = sum(
            1 for (rlat, rlon) in road_midpoints if haversine_km(lat, lon, rlat, rlon) <= ROAD_BUFFER_KM
        )
 
        result = compute_source_attribution(
            point_name=name, lat=lat, lon=lon,
            traffic_row=traffic_row,
            wind_speed=float(weather_row["wind_speed"]), wind_deg=float(weather_row["wind_deg"]),
            industrial_zones=industrial_zones, construction_zones=construction_zones,
            road_points_nearby=road_count_nearby, ref_time=ref_time,
        )
        results.append(result)
 
    _attribution_cache = results
    _attribution_cache_time = now
    return results
 
 
if __name__ == "__main__":
    results = run_for_all_points()
    for r in results:
        print(f"\n{r['point']}:")
        for k, v in r["sources"].items():
            print(f"  {k}: {v}%")
        print(f"  (congestion_ratio={r['raw_signals']['congestion_ratio']}, "
              f"wind={r['raw_signals']['wind_speed_mps']}m/s @ {r['raw_signals']['wind_deg']}°, "
              f"stubble_season={r['raw_signals']['is_stubble_burning_season']})")