

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
LIVE_POLLUTANTS_LOG = BASE_DIR / "live_pollutants_log.csv"
LIVE_GROUND_AQI_LOG = BASE_DIR / "live_ground_aqi_log.csv"

REQUIRED_HOURS_FOR_FULL_FORECAST = 168  # 7 days -- see module docstring


def _load_csv_safe(path: Path, parse_col: str = "timestamp") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, parse_dates=[parse_col])
    except (pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame()
    return df


def get_live_history() -> pd.DataFrame:
    """Builds the live, hourly-resampled history across all cities. Reads
    both CSVs fresh every call -- always reflects whatever the collectors
    have written so far, no restart needed."""
    aqi_df = _load_csv_safe(LIVE_GROUND_AQI_LOG)
    poll_df = _load_csv_safe(LIVE_POLLUTANTS_LOG)

    if aqi_df.empty:
        return pd.DataFrame(columns=[
            "timestamp", "location_name", "location_lat", "location_lon",
            "co", "no2", "o3", "pm10", "pm25", "so2", "aqi", "aqi_category",
            "hour", "day_of_week", "month", "year", "is_weekend",
        ])

    aqi_df = aqi_df.rename(columns={"lat": "location_lat", "lon": "location_lon"}) \
        if "lat" in aqi_df.columns else aqi_df
    aqi_df = aqi_df.sort_values(["location_name", "timestamp"])

    if not poll_df.empty:
        poll_df = poll_df.rename(columns={"lat": "location_lat", "lon": "location_lon"}) \
            if "lat" in poll_df.columns else poll_df
        poll_df = poll_df.sort_values(["location_name", "timestamp"])
        merged_parts = []
        for city, city_aqi in aqi_df.groupby("location_name"):
            city_poll = poll_df[poll_df["location_name"] == city]
            if city_poll.empty:
                city_merged = city_aqi.copy()
                for col in ["co", "no2", "o3", "pm10", "pm25", "so2"]:
                    city_merged[col] = np.nan
            else:
                city_merged = pd.merge_asof(
                    city_aqi, city_poll[["timestamp", "co", "no2", "o3", "pm10", "pm25", "so2"]],
                    on="timestamp", direction="nearest",
                    tolerance=pd.Timedelta("2h"),
                )
            merged_parts.append(city_merged)
        merged = pd.concat(merged_parts, ignore_index=True)
    else:
        merged = aqi_df.copy()
        for col in ["co", "no2", "o3", "pm10", "pm25", "so2"]:
            merged[col] = np.nan

    merged["hour_bucket"] = merged["timestamp"].dt.floor("h")

    hourly = (
        merged.sort_values("timestamp")
        .drop(columns=["timestamp"])
        .groupby(["location_name", "hour_bucket"], as_index=False)
        .last()
    )
    hourly = hourly.rename(columns={"hour_bucket": "timestamp"})

    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["day_of_week"] = hourly["timestamp"].dt.dayofweek
    hourly["month"] = hourly["timestamp"].dt.month
    hourly["year"] = hourly["timestamp"].dt.year
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)

    keep_cols = [
        "timestamp", "location_name", "location_lat", "location_lon",
        "co", "no2", "o3", "pm10", "pm25", "so2", "aqi", "aqi_category",
        "hour", "day_of_week", "month", "year", "is_weekend",
    ]
    hourly = hourly[[c for c in keep_cols if c in hourly.columns]]
    return hourly.sort_values(["location_name", "timestamp"]).reset_index(drop=True)


def coverage_hours(live_df: pd.DataFrame, city: str) -> int:
    """How many hourly data points exist for this city right now. Use this
    to decide whether to show a 'still collecting data' warm-up notice."""
    if live_df.empty:
        return 0
    return int((live_df["location_name"] == city).sum())
