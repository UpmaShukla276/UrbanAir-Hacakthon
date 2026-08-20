"""
Forecast Engine v1 — 24 / 48 / 72-hour ahead AQI forecasting
==============================================================
Unlike the nowcasting model (aqi_regressor.pkl), this predicts FUTURE AQI
using only information that would actually be available in advance:
  - AQI's own historical pattern (lag features, rolling stats)
  - Cyclic time features (hour/day/month -- captures rush hour, seasonal
    stubble-burning spikes, etc.)
  - City identity

It deliberately does NOT use same-timestamp pollutant concentrations as
inputs (unlike the nowcasting model) since those won't be known ahead of
time either -- that would be leakage in a real forecasting deployment.

Three separate models are trained (one per horizon) because the right
lag structure differs: predicting 24h ahead can lean on yesterday's same
hour, but 72h ahead needs to lean more on weekly seasonality.
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb

DATA_PATH = "processed_aqi_data.csv"
MODEL_DIR = Path("models_forecast")
MODEL_DIR.mkdir(exist_ok=True)

HORIZONS = [24, 48, 72]  # hours ahead

# ---------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------
print("Loading data...")
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
df = df.sort_values(["location_name", "timestamp"]).reset_index(drop=True)
print(f"Rows: {len(df):,} | Cities: {df['location_name'].unique().tolist()}")

# ---------------------------------------------------------------
# 2. Feature engineering (per city, so lags don't leak across cities)
# ---------------------------------------------------------------
print("Building lag/rolling features...")


def build_features(city_df):
    city_df = city_df.sort_values("timestamp").reset_index(drop=True)

    # --- Lag features on AQI itself ---
    city_df["aqi_lag_1h"] = city_df["aqi"].shift(1)
    city_df["aqi_lag_24h"] = city_df["aqi"].shift(24)
    city_df["aqi_lag_48h"] = city_df["aqi"].shift(48)
    city_df["aqi_lag_72h"] = city_df["aqi"].shift(72)
    city_df["aqi_lag_168h"] = city_df["aqi"].shift(168)  # same hour, 1 week ago

    # --- Rolling stats (shifted by 1 first, so "now" isn't included in its own window) ---
    shifted = city_df["aqi"].shift(1)
    city_df["aqi_roll_mean_24h"] = shifted.rolling(24).mean()
    city_df["aqi_roll_std_24h"] = shifted.rolling(24).std()
    city_df["aqi_roll_mean_168h"] = shifted.rolling(168).mean()
    city_df["aqi_roll_max_24h"] = shifted.rolling(24).max()

    # --- Short-term trend: is AQI rising or falling right now? ---
    city_df["aqi_trend_6h"] = city_df["aqi_lag_1h"] - city_df["aqi"].shift(7)

    # --- Key pollutant lags too (PM2.5/PM10 often lead AQI moves, e.g. stubble burning) ---
    for pol in ["pm25", "pm10"]:
        city_df[f"{pol}_lag_24h"] = city_df[pol].shift(24)
        city_df[f"{pol}_roll_mean_24h"] = city_df[pol].shift(1).rolling(24).mean()

    # --- Forecast targets: AQI N hours in the FUTURE ---
    for h in HORIZONS:
        city_df[f"target_{h}h"] = city_df["aqi"].shift(-h)

    return city_df


city_frames = []
for city in df["location_name"].unique():
    city_frames.append(build_features(df[df["location_name"] == city].copy()))
df = pd.concat(city_frames, ignore_index=True)

# Cyclic time features (same as nowcasting model)
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

from sklearn.preprocessing import LabelEncoder
city_encoder = LabelEncoder()
df["city_code"] = city_encoder.fit_transform(df["location_name"])

LAG_FEATURES = [
    "aqi_lag_1h", "aqi_lag_24h", "aqi_lag_48h", "aqi_lag_72h", "aqi_lag_168h",
    "aqi_roll_mean_24h", "aqi_roll_std_24h", "aqi_roll_mean_168h", "aqi_roll_max_24h",
    "aqi_trend_6h", "pm25_lag_24h", "pm25_roll_mean_24h", "pm10_lag_24h", "pm10_roll_mean_24h",
    "hour_sin", "hour_cos", "month_sin", "month_cos", "dow_sin", "dow_cos",
    "is_weekend", "city_code", "location_lat", "location_lon", "year",
]

# Drop rows where lag/lead features are NaN (start/end of each city's series)
df_clean = df.dropna(subset=LAG_FEATURES + [f"target_{h}h" for h in HORIZONS]).reset_index(drop=True)
print(f"Rows after building lags (dropped {len(df) - len(df_clean):,} edge rows): {len(df_clean):,}")

# ---------------------------------------------------------------
# 3. Time-based split
# ---------------------------------------------------------------
train_df = df_clean[df_clean["year"] <= 2022].copy()
test_df = df_clean[df_clean["year"] >= 2023].copy()
print(f"Train: {len(train_df):,} | Test: {len(test_df):,}")

# ---------------------------------------------------------------
# 4. Train one model per horizon
# ---------------------------------------------------------------
results = {}
models = {}

for h in HORIZONS:
    print(f"\nTraining {h}-hour ahead forecast model...")
    target_col = f"target_{h}h"
    X_train, y_train = train_df[LAG_FEATURES], train_df[target_col]
    X_test, y_test = test_df[LAG_FEATURES], test_df[target_col]

    model = lgb.LGBMRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=8,
        num_leaves=63, random_state=42, verbosity=-1
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    r2 = r2_score(y_test, pred)
    rmse = mean_squared_error(y_test, pred) ** 0.5
    mae = mean_absolute_error(y_test, pred)

    # Naive baseline for comparison: "tomorrow = same as last known value"
    naive_pred = test_df["aqi_lag_1h"]
    naive_mae = mean_absolute_error(y_test, naive_pred)

    results[f"{h}h"] = {"R2": r2, "RMSE": rmse, "MAE": mae, "naive_baseline_MAE": naive_mae}
    models[h] = model
    joblib.dump(model, MODEL_DIR / f"forecast_{h}h.pkl", compress=3)
    print(f"  R2={r2:.4f}  RMSE={rmse:.2f}  MAE={mae:.2f}  (naive baseline MAE={naive_mae:.2f})")

# ---------------------------------------------------------------
# 5. Save artifacts
# ---------------------------------------------------------------
joblib.dump(city_encoder, MODEL_DIR / "city_encoder.pkl")

meta = {
    "features": LAG_FEATURES,
    "horizons": HORIZONS,
    "metrics": results,
    "cities": city_encoder.classes_.tolist(),
    "train_years": "2019-2022",
    "test_years": "2023-2024",
    "note": "Forecast models use only lag/rolling AQI history + pollutant lags + "
            "cyclic time features -- no same-timestamp pollutant readings, since "
            "those aren't known in advance in a real deployment.",
}
with open(MODEL_DIR / "metadata.json", "w") as f:
    json.dump(meta, f, indent=2)

print("\n=== Summary ===")
for h in HORIZONS:
    m = results[f"{h}h"]
    improvement = 100 * (1 - m["MAE"] / m["naive_baseline_MAE"])
    print(f"{h}h ahead: R2={m['R2']:.4f} MAE={m['MAE']:.2f} "
          f"(vs naive {m['naive_baseline_MAE']:.2f}, {improvement:.1f}% better)")

print(f"\nSaved to {MODEL_DIR}/")
