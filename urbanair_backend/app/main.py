"""
UrbanAir AI — FastAPI Backend
==============================
Serves the ML models (nowcast + forecast) and geospatial data to the
React dashboard.

Run:
    uvicorn app.main:app --reload --port 8000

Endpoints:
    GET  /api/health
    GET  /api/cities
    GET  /api/current/{city}                     -> latest known AQI (simulated "live")
    POST /api/nowcast                             -> AQI from pollutant readings
    GET  /api/forecast/{city}                     -> 24/48/72h forecast from latest known state
    GET  /api/historical/{city}?hours=168         -> time series for trend charts
    GET  /api/geojson/{layer}                     -> parks | residential | industrial | roads
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import source_attribution as sa
import green_cover as gc
import live_history
from . import alert_generator
from . import notifications
from . import groq_arbiter

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="UrbanAir AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# Load artifacts once at startup
# ---------------------------------------------------------------
nowcast_regressor = joblib.load(BASE_DIR / "models" / "aqi_regressor.pkl")
nowcast_classifier = joblib.load(BASE_DIR / "models" / "aqi_classifier.pkl")
nowcast_city_encoder = joblib.load(BASE_DIR / "models" / "city_encoder.pkl")
nowcast_meta = json.load(open(BASE_DIR / "models" / "metadata.json"))

forecast_models = {h: joblib.load(BASE_DIR / "models_forecast" / f"forecast_{h}h.pkl") for h in [24, 48, 72]}
forecast_city_encoder = joblib.load(BASE_DIR / "models_forecast" / "city_encoder.pkl")
forecast_meta = json.load(open(BASE_DIR / "models_forecast" / "metadata.json"))

# NOTE: processed_aqi_data.csv (frozen at Jan 2024) is no longer loaded here.
# /api/forecast and /api/historical now build their input from live_history.py,
# which reads the live WAQI + pollutant logs fresh on every call.

CITY_COORDS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}

AQI_CATEGORY_COLORS = {
    "Good": "#00A65A", "Satisfactory": "#8CC63F", "Moderate": "#FFC107",
    "Poor": "#FF7A00", "Very Poor": "#D9534F", "Severe": "#7B1F1F",
}

GEOJSON_FILES = {
    "parks": BASE_DIR / "delhi_ncr_parks.geojson",
    "residential": BASE_DIR / "delhi_ncr_residential.geojson",
    "industrial": BASE_DIR / "delhi_ncr_industrial.geojson",
    "construction": BASE_DIR / "delhi_ncr_construction.geojson",
    "roads": BASE_DIR / "delhi_ncr_major_roads.geojson",
}


# ---------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------
class NowcastRequest(BaseModel):
    city: str
    co: float
    no2: float
    o3: float
    pm10: float
    pm25: float
    so2: float
    timestamp: Optional[str] = None  # ISO format; defaults to now


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def aqi_category_from_value(aqi_val: float) -> str:
    if aqi_val <= 50:
        return "Good"
    elif aqi_val <= 100:
        return "Satisfactory"
    elif aqi_val <= 200:
        return "Moderate"
    elif aqi_val <= 300:
        return "Poor"
    elif aqi_val <= 400:
        return "Very Poor"
    return "Severe"


def build_forecast_features_for_row(city_df: pd.DataFrame, idx: int) -> dict:
    row = city_df.iloc[idx]
    aqi_series = city_df["aqi"]

    def safe_shift(offset):
        j = idx - offset
        return float(aqi_series.iloc[j]) if j >= 0 else np.nan

    shifted = aqi_series.shift(1)
    feats = {
        "aqi_lag_1h": safe_shift(1),
        "aqi_lag_24h": safe_shift(24),
        "aqi_lag_48h": safe_shift(48),
        "aqi_lag_72h": safe_shift(72),
        "aqi_lag_168h": safe_shift(168),
        "aqi_roll_mean_24h": shifted.iloc[max(0, idx - 24):idx].mean() if idx >= 24 else np.nan,
        "aqi_roll_std_24h": shifted.iloc[max(0, idx - 24):idx].std() if idx >= 24 else np.nan,
        "aqi_roll_mean_168h": shifted.iloc[max(0, idx - 168):idx].mean() if idx >= 168 else np.nan,
        "aqi_roll_max_24h": shifted.iloc[max(0, idx - 24):idx].max() if idx >= 24 else np.nan,
        "aqi_trend_6h": (safe_shift(1) - safe_shift(7)) if idx >= 7 else np.nan,
        "pm25_lag_24h": float(city_df["pm25"].iloc[idx - 24]) if idx >= 24 else np.nan,
        "pm25_roll_mean_24h": city_df["pm25"].shift(1).iloc[max(0, idx - 24):idx].mean() if idx >= 24 else np.nan,
        "pm10_lag_24h": float(city_df["pm10"].iloc[idx - 24]) if idx >= 24 else np.nan,
        "pm10_roll_mean_24h": city_df["pm10"].shift(1).iloc[max(0, idx - 24):idx].mean() if idx >= 24 else np.nan,
        "hour_sin": np.sin(2 * np.pi * row["hour"] / 24),
        "hour_cos": np.cos(2 * np.pi * row["hour"] / 24),
        "month_sin": np.sin(2 * np.pi * row["month"] / 12),
        "month_cos": np.cos(2 * np.pi * row["month"] / 12),
        "dow_sin": np.sin(2 * np.pi * row["day_of_week"] / 7),
        "dow_cos": np.cos(2 * np.pi * row["day_of_week"] / 7),
        "is_weekend": row["is_weekend"],
        "location_lat": row["location_lat"],
        "location_lon": row["location_lon"],
        "year": row["year"],
    }
    return feats


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/api/cities")
def get_cities():
    return [
        {"name": name, "lat": lat, "lon": lon}
        for name, (lat, lon) in CITY_COORDS.items()
    ]


LIVE_POLLUTANTS_LOG = BASE_DIR / "live_pollutants_log.csv"
LIVE_GROUND_AQI_LOG = BASE_DIR / "live_ground_aqi_log.csv"


def _load_latest_live_pollutants(city: str):
    """Reads live_pollutants_log.csv (written by aqi_model/air_pollution_collector.py)
    fresh on every call -- no caching -- so a new row shows up without a
    backend restart. Returns None if the file doesn't exist yet or has no
    rows for this city."""
    if not LIVE_POLLUTANTS_LOG.exists():
        return None
    try:
        live_df = pd.read_csv(LIVE_POLLUTANTS_LOG, parse_dates=["timestamp"])
    except (pd.errors.EmptyDataError, ValueError):
        return None
    city_rows = live_df[live_df["location_name"] == city]
    if city_rows.empty:
        return None
    return city_rows.sort_values("timestamp").iloc[-1]


def _load_latest_ground_aqi(city: str):
    """Reads live_ground_aqi_log.csv (written by aqi_model/waqi_aqi_collector.py)
    fresh on every call. This is real CPCB ground-station AQI (via aqicn.org),
    more accurate for a hotspot-heavy city than a regional model estimate.
    Returns None if the file doesn't exist yet or has no rows for this city."""
    if not LIVE_GROUND_AQI_LOG.exists():
        return None
    try:
        live_df = pd.read_csv(LIVE_GROUND_AQI_LOG, parse_dates=["timestamp"])
    except (pd.errors.EmptyDataError, ValueError):
        return None
    city_rows = live_df[live_df["location_name"] == city]
    if city_rows.empty:
        return None
    return city_rows.sort_values("timestamp").iloc[-1]


@app.get("/api/current/{city}")
def get_current(city: str):
    """Returns the most recent AQI reading for a city.

    Both live sources are computed when available:
      - WAQI ground-station AQI (aqi_model/waqi_aqi_collector.py) -- real
        CPCB monitor data.
      - Nowcast model prediction from live OWM pollutant concentrations
        (aqi_model/air_pollution_collector.py) -- your trained
        aqi_regressor.pkl / aqi_classifier.pkl.

    If they roughly agree, WAQI is used directly (it's real ground-truth
    when available -- no need to call an LLM to agree with itself). If they
    diverge by more than 15%, Groq is asked to arbitrate which one is more
    plausible given context (pollutant mix, recent trend, model's known
    error rate) -- see groq_arbiter.py for exactly what that can and can't
    tell you. The `arbitration` field in the response is always included so
    the frontend can show it transparently, never silently.

    No static-file fallback: if neither live source is available for this
    city right now, this returns 503 rather than quietly serving old data
    as if it were current."""
    if city not in CITY_COORDS:
        raise HTTPException(404, f"Unknown city: {city}")

    live_pollutants = _load_latest_live_pollutants(city)
    ground_aqi_row = _load_latest_ground_aqi(city)

    if ground_aqi_row is None and live_pollutants is None:
        raise HTTPException(
            503,
            f"No live data available yet for {city}. Run aqi_model/run_all.py "
            f"and wait a minute or two for the first collector rows to land."
        )

    model_aqi = model_category = None
    if live_pollutants is not None:
        co, no2, o3 = float(live_pollutants["co"]), float(live_pollutants["no2"]), float(live_pollutants["o3"])
        pm10, pm25, so2 = float(live_pollutants["pm10"]), float(live_pollutants["pm25"]), float(live_pollutants["so2"])
        pollutant_ts = live_pollutants["timestamp"]
        model_aqi, model_category = _predict_aqi_from_pollutants(city, co, no2, o3, pm10, pm25, so2, pollutant_ts.to_pydatetime())
        pollutants = {"co": co, "no2": no2, "o3": o3, "pm10": pm10, "pm25": pm25, "so2": so2}
    else:
        pollutant_ts = None
        pollutants = None

    arbitration = None
    if ground_aqi_row is not None and model_aqi is not None:
        waqi_aqi, waqi_category = float(ground_aqi_row["aqi"]), ground_aqi_row["aqi_category"]
        if groq_arbiter.needs_arbitration(waqi_aqi, model_aqi):
            live_hist = live_history.get_live_history()
            city_hist = live_hist[live_hist["location_name"] == city].tail(24)
            recent_trend = [round(float(v), 1) for v in city_hist["aqi"].tolist()]
            arbitration = groq_arbiter.arbitrate(
                city, waqi_aqi, waqi_category, model_aqi, model_category,
                pollutants, nowcast_meta["regression_metrics"][nowcast_meta["best_regressor"]]["MAE"],
                recent_trend,
            )
            aqi_val, category = arbitration["final_aqi"], arbitration["final_category"]
            data_as_of = ground_aqi_row["timestamp"] if arbitration["chosen"] == "waqi" else pollutant_ts
        else:
            aqi_val, category, data_as_of = waqi_aqi, waqi_category, ground_aqi_row["timestamp"]
    elif ground_aqi_row is not None:
        aqi_val, category, data_as_of = float(ground_aqi_row["aqi"]), ground_aqi_row["aqi_category"], ground_aqi_row["timestamp"]
    else:
        aqi_val, category, data_as_of = model_aqi, model_category, pollutant_ts

    is_estimated = False  # both sources here are live; no static fallback left

    if pollutants is None:
        pollutants = {"co": None, "no2": None, "o3": None, "pm10": None, "pm25": None, "so2": None}

    return {
        "city": city,
        "arbitration": arbitration,
        "timestamp": datetime.now().isoformat(),
        "data_as_of": data_as_of.isoformat(),
        "is_estimated": is_estimated,
        "aqi": round(aqi_val, 1),
        "category": category,
        "color": AQI_CATEGORY_COLORS.get(category, "#888888"),
        "pollutants": pollutants,
    }



def _predict_aqi_from_pollutants(city: str, co: float, no2: float, o3: float, pm10: float, pm25: float, so2: float, dt: datetime):
    """Shared nowcast logic: pollutant concentrations -> (aqi, category) using
    the trained regressor + classifier. Used by both /api/nowcast (manual
    entry) and get_current (live sensor feed)."""
    lat, lon = CITY_COORDS[city]
    hour, month, dow = dt.hour, dt.month, dt.weekday()
    is_weekend = 1 if dow >= 5 else 0
    city_code = nowcast_city_encoder.transform([city])[0]

    features = pd.DataFrame([{
        "co": co, "no2": no2, "o3": o3, "pm10": pm10, "pm25": pm25, "so2": so2,
        "hour_sin": np.sin(2 * np.pi * hour / 24), "hour_cos": np.cos(2 * np.pi * hour / 24),
        "month_sin": np.sin(2 * np.pi * month / 12), "month_cos": np.cos(2 * np.pi * month / 12),
        "dow_sin": np.sin(2 * np.pi * dow / 7), "dow_cos": np.cos(2 * np.pi * dow / 7),
        "is_weekend": is_weekend, "city_code": city_code,
        "location_lat": lat, "location_lon": lon, "year": dt.year,
    }])[nowcast_meta["features"]]

    pred_aqi = float(nowcast_regressor.predict(features)[0])
    pred_category = nowcast_classifier.predict(features)[0]
    if isinstance(pred_category, np.ndarray):
        pred_category = pred_category[0]
    return pred_aqi, pred_category


@app.post("/api/nowcast")
def nowcast(req: NowcastRequest):
    if req.city not in CITY_COORDS:
        raise HTTPException(404, f"Unknown city: {req.city}")

    dt = datetime.fromisoformat(req.timestamp) if req.timestamp else datetime.now()
    pred_aqi, pred_category = _predict_aqi_from_pollutants(
        req.city, req.co, req.no2, req.o3, req.pm10, req.pm25, req.so2, dt
    )

    return {
        "city": req.city,
        "aqi": round(pred_aqi, 1),
        "category": pred_category,
        "color": AQI_CATEGORY_COLORS.get(pred_category, "#888888"),
    }


@app.get("/api/forecast/{city}")
def forecast(city: str, reference_time: Optional[str] = None):
    """24/48/72hr forecast, built from the LIVE accumulating history
    (live_history.py) instead of the old frozen Jan-2024 CSV.

    Honesty note: the model needs up to 168 hours (7 days) of hourly lag
    history for full accuracy (aqi_lag_168h, aqi_roll_mean_168h, etc).
    Right after a fresh deployment there won't be 7 days of live data yet --
    `data_maturity` in the response tells you exactly how many hours are
    available right now vs the 168 needed. Missing lag features are left as
    NaN; LightGBM (the trained regressor) handles NaN natively, so you still
    get a prediction during warm-up, just built on less context than it was
    validated with -- don't present it as full-confidence until maturity
    reaches 168h."""
    if city not in CITY_COORDS:
        raise HTTPException(404, f"Unknown city: {city}")

    live_df = live_history.get_live_history()
    city_df = live_df[live_df["location_name"] == city].reset_index(drop=True)

    if city_df.empty:
        raise HTTPException(
            503,
            f"No live history yet for {city}. Run aqi_model/run_all.py "
            f"at least once -- forecast needs live data to build from."
        )

    if reference_time:
        target_ts = pd.to_datetime(reference_time)
        idx = int((city_df["timestamp"] - target_ts).abs().idxmin())
    else:
        idx = len(city_df) - 1

    hours_available = idx + 1
    data_maturity = {
        "hours_available": hours_available,
        "hours_needed_for_full_accuracy": live_history.REQUIRED_HOURS_FOR_FULL_FORECAST,
        "is_warming_up": hours_available < live_history.REQUIRED_HOURS_FOR_FULL_FORECAST,
    }

    feats = build_forecast_features_for_row(city_df, idx)
    feats["city_code"] = forecast_city_encoder.transform([city])[0]
    X = pd.DataFrame([feats])[forecast_meta["features"]]

    current_aqi = float(city_df.loc[idx, "aqi"])
    reference_ts = city_df.loc[idx, "timestamp"].isoformat()

    predictions = []
    for h in [24, 48, 72]:
        pred = float(forecast_models[h].predict(X)[0])
        future_idx = idx + h
        actual = float(city_df.loc[future_idx, "aqi"]) if future_idx < len(city_df) else None
        predictions.append({
            "horizon_hours": h,
            "predicted_aqi": round(pred, 1),
            "predicted_category": aqi_category_from_value(pred),
            "color": AQI_CATEGORY_COLORS.get(aqi_category_from_value(pred), "#888888"),
            "actual_aqi": round(actual, 1) if actual is not None else None,
        })

    return {
        "city": city,
        "reference_time": reference_ts,
        "current_aqi": round(current_aqi, 1),
        "forecasts": predictions,
        "model_metrics": forecast_meta["metrics"],
        "data_maturity": data_maturity,
    }


@app.get("/api/historical/{city}")
def historical(city: str, hours: int = 168):
    """Trend-chart series, built from the LIVE accumulating history. Early
    on this will return fewer points than `hours` asked for -- it grows as
    the collectors keep running, it doesn't backfill from static data."""
    if city not in CITY_COORDS:
        raise HTTPException(404, f"Unknown city: {city}")

    live_df = live_history.get_live_history()
    city_df = live_df[live_df["location_name"] == city].tail(hours)
    return [
        {
            "timestamp": row["timestamp"].isoformat(),
            "aqi": round(float(row["aqi"]), 1),
            "category": row["aqi_category"],
            "pm25": round(float(row["pm25"]), 1) if pd.notna(row["pm25"]) else None,
            "pm10": round(float(row["pm10"]), 1) if pd.notna(row["pm10"]) else None,
        }
        for _, row in city_df.iterrows()
    ]



@app.get("/api/geojson/{layer}")
def geojson_layer(layer: str):
    if layer not in GEOJSON_FILES:
        raise HTTPException(404, f"Unknown layer: {layer}. Choose from {list(GEOJSON_FILES.keys())}")
    with open(GEOJSON_FILES[layer]) as f:
        return json.load(f)


@app.get("/api/source-attribution")
def source_attribution_all():
    """Rule-based source attribution (Traffic / Industrial / Construction /
    Waste-Burning / Background) for all monitored points. Requires
    traffic_log.csv and weather_current_log.csv to have at least one
    logged snapshot (run traffic_collector.py / weather_collector.py first)."""
    try:
        return sa.run_for_all_points()
    except FileNotFoundError as e:
        raise HTTPException(
            503,
            f"Missing data file: {e.filename}. Run traffic_collector.py and "
            f"weather_collector.py at least once to generate the logs."
        )


@app.get("/api/source-attribution/{point}")
def source_attribution_point(point: str):
    results = source_attribution_all()
    for r in results:
        if r["point"].lower() == point.lower():
            return r
    raise HTTPException(404, f"Unknown point: {point}. Choose from {list(sa.CITY_COORDS.keys())}")


@app.get("/api/enforcement")
def enforcement_intelligence():
    """Ranks all monitored points by priority for inspection/enforcement,
    combining: current + forecasted AQI severity + dominant pollution
    source + current traffic congestion. Rule-based (transparent, not a
    black box) -- this is exactly the kind of reasoning an official would
    want to see justified, not just a ranked list.

    Ranking uses the WORSE of "AQI right now" and "+24h forecast", not the
    forecast alone. Reason: the forecast model needs up to 168 hours of
    live lag history to be fully trained on this deployment's own data
    (see live_history.py) -- a freshly-started system may not have that
    yet, during which the forecast can swing far from current reality.
    An official needs to act on severe pollution happening RIGHT NOW even
    if a still-warming-up forecast optimistically predicts improvement.
    `forecast_is_warming_up` on each item tells the frontend whether the
    +24h number should be shown with reduced confidence."""
    attribution_results = source_attribution_all()

    priorities = []
    for attr in attribution_results:
        point = attr["point"]
        # Use nearest known city for AQI forecast (hotspots reuse their nearest city's AQI series)
        point_lat, point_lon = sa.CITY_COORDS[point]
        city_for_aqi, _ = sa.nearest_known_city(point_lat, point_lon)
        try:
            fc = forecast(city_for_aqi)
            forecast_24h = next(f for f in fc["forecasts"] if f["horizon_hours"] == 24)
            aqi_24h = forecast_24h["predicted_aqi"]
            current_aqi = fc["current_aqi"]
            forecast_is_warming_up = fc["data_maturity"]["is_warming_up"]
        except Exception:
            aqi_24h = None
            current_aqi = None
            forecast_is_warming_up = None

        candidate_aqis = [v for v in (current_aqi, aqi_24h) if v is not None]
        aqi_for_ranking = max(candidate_aqis) if candidate_aqis else 150

        sources = attr["sources"]
        dominant_source = max(
            (k for k in sources if k != "background_pct"),
            key=lambda k: sources[k]
        )
        congestion_ratio = attr["raw_signals"]["congestion_ratio"]

        # Priority score: weighted combination, higher = more urgent
        severity_component = aqi_for_ranking / 500.0  # normalize against CPCB practical max
        congestion_component = max(0.0, 1.0 - congestion_ratio)
        source_intensity = max(v for k, v in sources.items() if k != "background_pct") / 100.0

        priority_score = round(100 * (0.5 * severity_component + 0.25 * congestion_component + 0.25 * source_intensity), 1)

        reasons = []
        if congestion_ratio < 0.75:
            reasons.append("Heavy traffic congestion")
        if sources["industrial_pct"] > 15:
            reasons.append("Significant industrial contribution")
        if sources["construction_pct"] > 10:
            reasons.append("Active construction dust")
        if sources["waste_burning_pct"] > 20:
            reasons.append("Waste/stubble burning signal")
        if current_aqi and current_aqi > 200:
            reasons.append(f"AQI currently at {round(current_aqi)} ({aqi_category_from_value(current_aqi)})")
        if aqi_24h and aqi_24h > 200:
            reasons.append(f"AQI forecast to reach {round(aqi_24h)} (Poor+) within 24h")
        if not reasons:
            reasons.append("No acute signal -- routine monitoring sufficient")

        actions = []
        if sources["traffic_pct"] > 30:
            actions.append("Deploy traffic police / restrict heavy vehicles")
        if sources["construction_pct"] > 10:
            actions.append("Inspect construction sites for dust-control compliance")
        if sources["industrial_pct"] > 15:
            actions.append("Inspect nearby industrial units for emission compliance")
        if sources["waste_burning_pct"] > 20:
            actions.append("Coordinate with neighboring state agencies on stubble burning")
        if not actions:
            actions.append("Continue routine monitoring")

        priorities.append({
            "point": point,
            "priority_score": priority_score,
            "current_aqi": round(current_aqi, 1) if current_aqi is not None else None,
            "forecast_aqi_24h": round(aqi_24h, 1) if aqi_24h is not None else None,
            "forecast_is_warming_up": forecast_is_warming_up,
            "dominant_source": dominant_source.replace("_pct", ""),
            "reasons": reasons,
            "recommended_actions": actions,
            "sources": sources,
        })

    priorities.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, p in enumerate(priorities):
        p["rank"] = i + 1

    return priorities


# CPCB-published health advisories per AQI band (National Air Quality Index).
HEALTH_ADVISORY_TABLE = {
    "Good": {
        "general": "Air quality is satisfactory. Enjoy outdoor activities.",
        "sensitive": "No precautions needed.",
    },
    "Satisfactory": {
        "general": "Air quality is acceptable. Minor discomfort possible for unusually sensitive people.",
        "sensitive": "Consider reducing prolonged outdoor exertion if you notice symptoms.",
    },
    "Moderate": {
        "general": "May cause breathing discomfort to people with lung disease, children, and older adults.",
        "sensitive": "People with asthma, lung or heart disease should reduce prolonged outdoor exertion.",
    },
    "Poor": {
        "general": "May cause breathing discomfort to most people on prolonged exposure.",
        "sensitive": "Avoid prolonged outdoor exertion. Wear an N95 mask if you must go outside.",
    },
    "Very Poor": {
        "general": "May cause respiratory illness on prolonged exposure. Avoid outdoor activity.",
        "sensitive": "Avoid all outdoor physical activity. Schools should limit outdoor activities.",
    },
    "Severe": {
        "general": "Affects healthy people and seriously impacts those with existing diseases. Avoid outdoor exposure.",
        "sensitive": "Stay indoors. Use an air purifier if available. Seek medical advice if experiencing symptoms.",
    },
}


def _build_health_advisory_payload(current, fc):
    """Shared by the single-city and all-points endpoints so both stay
    in sync with one source of truth for the advisory text logic."""
    category = current["category"]
    advisory = HEALTH_ADVISORY_TABLE.get(category, HEALTH_ADVISORY_TABLE["Moderate"])

    horizon_advisories = []
    for f in fc["forecasts"]:
        cat = f["predicted_category"]
        horizon_advisories.append({
            "horizon_hours": f["horizon_hours"],
            "predicted_aqi": f["predicted_aqi"],
            "category": cat,
            "advisory": HEALTH_ADVISORY_TABLE.get(cat, HEALTH_ADVISORY_TABLE["Moderate"])["general"],
        })

    return {
        "current_aqi": current["aqi"],
        "current_category": category,
        "general_advisory": advisory["general"],
        "sensitive_groups_advisory": advisory["sensitive"],
        "forecast_advisories": horizon_advisories,
        "forecast_is_warming_up": fc["data_maturity"]["is_warming_up"],
    }


@app.get("/api/health-advisory/{city}")
def health_advisory(city: str):
    if city not in CITY_COORDS:
        raise HTTPException(404, f"Unknown city: {city}")

    current = get_current(city)
    fc = forecast(city)
    return {"city": city, **_build_health_advisory_payload(current, fc)}


@app.get("/api/health-advisory")
def health_advisory_all():
    """Health advisory for all 21 monitored points (5 trained cities +
    13 DPCC hotspots + 3 landmarks) -- the same point set used by Green
    Cover and Enforcement, so all tabs cover the same footprint.

    The 5 trained cities have live sensor/model readings. The other 16
    points don't have their own trained nowcast model, so AQI/forecast
    is proxied from the nearest trained city -- identical honest-proxy
    pattern already used by /api/estimate, with the same distance/label
    fields included so the frontend can show it transparently rather
    than implying false precision."""
    results = []
    for point, (lat, lon) in sa.CITY_COORDS.items():
        nearest_city, dist_km = sa.nearest_known_city(lat, lon)
        try:
            current = get_current(nearest_city)
            fc = forecast(nearest_city)
        except HTTPException:
            # nearest trained city has no live reading yet (still warming
            # up) -- skip this point rather than serving a stale/fake one
            continue

        payload = _build_health_advisory_payload(current, fc)
        results.append({
            "point": point,
            "is_directly_measured": point == nearest_city,
            "nearest_known_city": nearest_city,
            "distance_to_nearest_city_km": round(dist_km, 2),
            **payload,
        })
    return results


# ---------------------------------------------------------------
# Hyperlocal search: geocode + arbitrary-point estimate + what-if
# ---------------------------------------------------------------
NCR_BBOX = "76.698,28.908,77.704,28.099"  # left,top,right,bottom for Nominatim viewbox

import requests as _requests  # local alias to avoid confusion with FastAPI request objects


@app.get("/api/search-location")
def search_location(query: str):
    """Free-text location search restricted to the Delhi NCR bbox, via
    OpenStreetMap Nominatim (no API key needed). Lets the user search ANY
    place, not just the 5 pre-registered cities."""
    try:
        resp = _requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query, "format": "json", "limit": 8,
                "viewbox": NCR_BBOX, "bounded": 1,
            },
            headers={"User-Agent": "UrbanAirAI-Hackathon-Prototype/1.0"},
            timeout=8,
        )
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        raise HTTPException(503, f"Location search failed: {e}")

    return [
        {"name": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"])}
        for r in results
    ]


@app.get("/api/estimate")
def estimate_point(lat: float, lon: float):
    """Hyperlocal estimate for ANY lat/lon in Delhi NCR -- not just the 5
    trained cities. AQI/forecast are proxied from the nearest trained
    city (since we don't have live pollutant sensors everywhere), but
    Source Attribution is computed FRESH for the exact point using the
    static geospatial layers + nearest live traffic/weather -- that part
    is genuinely hyperlocal, not a nearest-neighbor copy."""
    nearest_city, dist_km = sa.nearest_known_city(lat, lon)

    proxy_current = get_current(nearest_city)
    proxy_forecast = forecast(nearest_city)

    try:
        traffic_log = pd.read_csv(BASE_DIR / "traffic_log.csv", parse_dates=["timestamp"])
        weather_log = pd.read_csv(BASE_DIR / "weather_current_log.csv", parse_dates=["fetch_timestamp"])
        industrial_zones, construction_zones, road_midpoints = sa.load_static_layers()
        attribution = sa.compute_for_arbitrary_point(
            lat, lon, traffic_log, weather_log, industrial_zones, construction_zones,
            road_midpoints, datetime.now()
        )
    except FileNotFoundError:
        attribution = None

    return {
        "lat": lat, "lon": lon,
        "nearest_known_city": nearest_city,
        "distance_to_nearest_city_km": round(dist_km, 2),
        "proxy_note": f"AQI/forecast values are proxied from {nearest_city} "
                      f"({round(dist_km, 1)} km away) -- no live sensor at this exact point.",
        "aqi": proxy_current["aqi"],
        "category": proxy_current["category"],
        "color": proxy_current["color"],
        "forecast": proxy_forecast["forecasts"],
        "source_attribution": attribution,
    }


class WhatIfRequest(BaseModel):
    point: str  # city or hotspot name from CITY_COORDS
    reduce_traffic_pct: float = 0
    reduce_industrial_pct: float = 0
    reduce_construction_pct: float = 0
    reduce_waste_burning_pct: float = 0


@app.post("/api/whatif")
def whatif(req: WhatIfRequest):
    if req.point not in sa.CITY_COORDS:
        raise HTTPException(404, f"Unknown point: {req.point}")

    attribution = source_attribution_point(req.point)
    point_lat, point_lon = sa.CITY_COORDS[req.point]
    city_for_aqi, _ = sa.nearest_known_city(point_lat, point_lon)
    current = get_current(city_for_aqi)

    reductions = {
        "traffic_pct": req.reduce_traffic_pct,
        "industrial_pct": req.reduce_industrial_pct,
        "construction_pct": req.reduce_construction_pct,
        "waste_burning_pct": req.reduce_waste_burning_pct,
    }
    return sa.compute_whatif(attribution, current["aqi"], reductions)


# ---------------------------------------------------------------
# Alerts / Notifications
# ---------------------------------------------------------------
def _get_alert_context(point):
    if point not in sa.CITY_COORDS:
        raise HTTPException(404, f"Unknown point: {point}")

    point_lat, point_lon = sa.CITY_COORDS[point]
    city_for_aqi, _ = sa.nearest_known_city(point_lat, point_lon)

    current = get_current(city_for_aqi)
    fc = forecast(city_for_aqi)
    attribution = source_attribution_point(point)

    enforcement_list = enforcement_intelligence()
    enforcement_entry = next((e for e in enforcement_list if e["point"] == point), None)

    return current, fc["forecasts"], attribution, enforcement_entry


@app.get("/api/alerts/officials/{point}")
def alert_for_officials(point: str):
    current, forecasts, attribution, enforcement_entry = _get_alert_context(point)
    report = alert_generator.generate_official_report(
        point, current["aqi"], current["category"], forecasts, attribution, enforcement_entry
    )
    return {"point": point, "report_text": report}


@app.get("/api/alerts/public/{point}")
def alert_for_public(point: str):
    current, forecasts, attribution, enforcement_entry = _get_alert_context(point)
    sources = attribution["sources"]
    dominant = max((k for k in sources if k != "background_pct"), key=lambda k: sources[k])
    dominant_label = dominant.replace("_pct", "").replace("_", " ").title()
    message = alert_generator.generate_public_advisory(point, current["aqi"], current["category"], dominant_label)
    return {"point": point, "message": message}


class SendAlertRequest(BaseModel):
    point: str
    alert_type: str  # "official" | "public"
    to_email: str


@app.get("/api/alerts/status")
def alert_send_status():
    return {"smtp_configured": notifications.is_configured()}


@app.post("/api/alerts/send")
def send_alert(req: SendAlertRequest):
    if req.alert_type == "official":
        content = alert_for_officials(req.point)
        subject = f"UrbanAir AI -- Enforcement Alert: {req.point}"
        body = content["report_text"]
    elif req.alert_type == "public":
        content = alert_for_public(req.point)
        subject = f"UrbanAir AI -- Air Quality Advisory: {req.point}"
        body = content["message"]
    else:
        raise HTTPException(400, "alert_type must be 'official' or 'public'")

    try:
        result = notifications.send_email(req.to_email, subject, body)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {e}")

    return {**result, "subject": subject}


# ---------------------------------------------------------------
# Green Cover Index ("Ek Ped Maa Ke Naam" alignment)
# ---------------------------------------------------------------
@app.get("/api/green-cover")
def green_cover_all():
    return gc.compute_for_all_points(sa.CITY_COORDS)


@app.get("/api/green-cover/{point}")
def green_cover_point(point: str):
    if point not in sa.CITY_COORDS:
        raise HTTPException(404, f"Unknown point: {point}")
    lat, lon = sa.CITY_COORDS[point]
    return gc.compute_green_cover_index(point, lat, lon)