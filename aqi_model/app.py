

import streamlit as st
import numpy as np
import pandas as pd
import joblib
import json
from datetime import datetime

st.set_page_config(page_title="AQI Predictor", page_icon="🌫️", layout="centered")



@st.cache_resource
def load_artifacts():
    regressor = joblib.load("models/aqi_regressor.pkl")
    classifier = joblib.load("models/aqi_classifier.pkl")
    city_encoder = joblib.load("models/city_encoder.pkl")
    with open("models/metadata.json") as f:
        meta = json.load(f)
    return regressor, classifier, city_encoder, meta


@st.cache_resource
def load_forecast_artifacts():
    models = {h: joblib.load(f"models_forecast/forecast_{h}h.pkl") for h in [24, 48, 72]}
    fc_city_encoder = joblib.load("models_forecast/city_encoder.pkl")
    with open("models_forecast/metadata.json") as f:
        fc_meta = json.load(f)
    return models, fc_city_encoder, fc_meta


@st.cache_data
def load_historical_data():
    df = pd.read_csv("processed_aqi_data.csv", parse_dates=["timestamp"])
    return df.sort_values(["location_name", "timestamp"]).reset_index(drop=True)


def build_forecast_features_for_row(city_df, idx):
    """Recreates the exact same lag/rolling features used in training, for one row."""
    row = city_df.iloc[idx]
    aqi_series = city_df["aqi"]

    def safe_shift(offset):
        j = idx - offset
        return aqi_series.iloc[j] if j >= 0 else np.nan

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
        "aqi_trend_6h": safe_shift(1) - safe_shift(7) if idx >= 7 else np.nan,
        "pm25_lag_24h": city_df["pm25"].iloc[idx - 24] if idx >= 24 else np.nan,
        "pm25_roll_mean_24h": city_df["pm25"].shift(1).iloc[max(0, idx - 24):idx].mean() if idx >= 24 else np.nan,
        "pm10_lag_24h": city_df["pm10"].iloc[idx - 24] if idx >= 24 else np.nan,
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


regressor, classifier, city_encoder, meta = load_artifacts()
fc_models, fc_city_encoder, fc_meta = load_forecast_artifacts()

CITY_COORDS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}

AQI_COLORS = {
    "Good": "#00A65A",
    "Satisfactory": "#8CC63F",
    "Moderate": "#FFC107",
    "Poor": "#FF7A00",
    "Very Poor": "#D9534F",
    "Severe": "#7B1F1F",
}


def aqi_to_color(aqi_val):
    if aqi_val <= 50:
        return AQI_COLORS["Good"]
    elif aqi_val <= 100:
        return AQI_COLORS["Satisfactory"]
    elif aqi_val <= 200:
        return AQI_COLORS["Moderate"]
    elif aqi_val <= 300:
        return AQI_COLORS["Poor"]
    elif aqi_val <= 400:
        return AQI_COLORS["Very Poor"]
    return AQI_COLORS["Severe"]


# ---------------------------------------------------------------
# UI
# ---------------------------------------------------------------
st.title("🌫️ AQI Predictor — Delhi NCR")
st.caption("Trained on 2019–2024 hourly NCR data (Delhi, Faridabad, Ghaziabad, Gurgaon, Noida).")

tab_now, tab_forecast = st.tabs(["📍 Nowcast", "🔮 Forecast (24/48/72hr)"])


with tab_now:
    with st.sidebar:
        st.header("Nowcast model info")
        st.write(f"**Deployed model:** {meta['best_regressor']}")
        r2 = meta["regression_metrics"][meta["best_regressor"]]["R2"]
        st.write(f"**Test R²:** {r2:.4f}")
        st.write(f"**Classifier accuracy:** {meta['classifier_accuracy']:.4f}")

    st.subheader("1. Location & time")
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("City", meta["cities"], index=0, key="now_city")
    with col2:
        d = st.date_input("Date", value=datetime.now().date(), key="now_date")
        t = st.time_input("Time", value=datetime.now().time(), key="now_time")
        dt = datetime.combine(d, t)

    st.subheader("2. Pollutant concentrations (µg/m³, CO in mg/m³)")
    c1, c2, c3 = st.columns(3)
    with c1:
        co = st.number_input("CO", min_value=0.0, value=1.0, step=0.1)
        pm25 = st.number_input("PM2.5", min_value=0.0, value=60.0, step=1.0)
    with c2:
        no2 = st.number_input("NO2", min_value=0.0, value=25.0, step=1.0)
        so2 = st.number_input("SO2", min_value=0.0, value=6.0, step=0.5)
    with c3:
        o3 = st.number_input("O3", min_value=0.0, value=30.0, step=1.0)
        pm10 = st.number_input("PM10", min_value=0.0, value=90.0, step=1.0)

    if st.button("Predict AQI", type="primary", use_container_width=True):
        lat, lon = CITY_COORDS[city]
        hour, month, dow = dt.hour, dt.month, dt.weekday()
        is_weekend = 1 if dow >= 5 else 0
        city_code = city_encoder.transform([city])[0]

        features = pd.DataFrame([{
            "co": co, "no2": no2, "o3": o3, "pm10": pm10, "pm25": pm25, "so2": so2,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "month_sin": np.sin(2 * np.pi * month / 12),
            "month_cos": np.cos(2 * np.pi * month / 12),
            "dow_sin": np.sin(2 * np.pi * dow / 7),
            "dow_cos": np.cos(2 * np.pi * dow / 7),
            "is_weekend": is_weekend,
            "city_code": city_code,
            "location_lat": lat,
            "location_lon": lon,
            "year": dt.year,
        }])[meta["features"]]

        pred_aqi = float(regressor.predict(features)[0])
        pred_category = classifier.predict(features)[0]
        if isinstance(pred_category, np.ndarray):
            pred_category = pred_category[0]

        color = AQI_COLORS.get(pred_category, "#888888")
        st.markdown("---")
        st.markdown(
            f"""
            <div style="text-align:center; padding: 24px; border-radius: 12px; background:{color}22; border: 2px solid {color};">
                <div style="font-size:14px; color:#555;">Predicted AQI</div>
                <div style="font-size:56px; font-weight:800; color:{color};">{pred_aqi:.0f}</div>
                <div style="font-size:20px; font-weight:600; color:{color};">{pred_category}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"{city} · {dt.strftime('%d %b %Y, %I:%M %p')}")

    st.markdown("---")
    st.caption("Nowcasting model: LightGBM on pollutant sub-index + cyclic time + city features. "
               "Since AQI is a formula-derived function of pollutant concentrations, near-perfect "
               "accuracy here is expected, not overfitting.")


with tab_forecast:
    with st.sidebar:
        st.header("Forecast model info")
        for h in [24, 48, 72]:
            m = fc_meta["metrics"][f"{h}h"]
            st.write(f"**{h}h:** R²={m['R2']:.3f}, MAE={m['MAE']:.1f} "
                     f"(vs naive {m['naive_baseline_MAE']:.1f})")

    st.subheader("Simulate a forecast from historical data")
    st.caption("Pick a city and a past moment (from held-out 2023-2024 test data). "
               "The model only sees data up to that point -- then predicts 24/48/72hr "
               "ahead, and we show you the *actual* value that occurred, for comparison.")

    hist_df = load_historical_data()
    fc_city = st.selectbox("City", fc_meta["cities"], key="fc_city")

    city_df = hist_df[hist_df["location_name"] == fc_city].reset_index(drop=True)
    # Restrict to test period + leave room for 72h lookahead
    test_mask = (city_df["year"] >= 2023) & (city_df.index < len(city_df) - 72) & (city_df.index >= 168)
    valid_indices = city_df.index[test_mask]

    if len(valid_indices) == 0:
        st.warning("Not enough test-period data for this city.")
    else:
        min_ts = city_df.loc[valid_indices[0], "timestamp"]
        max_ts = city_df.loc[valid_indices[-1], "timestamp"]
        chosen_ts = st.slider(
            "Pick 'now' (from test period)",
            min_value=min_ts.to_pydatetime(), max_value=max_ts.to_pydatetime(),
            value=min_ts.to_pydatetime(), format="DD MMM YYYY, HH:mm"
        )
        # find closest matching row
        idx = (city_df["timestamp"] - chosen_ts).abs().idxmin()
        idx = int(idx)

        current_aqi = city_df.loc[idx, "aqi"]
        st.metric("Current AQI (at chosen moment)", f"{current_aqi:.0f}")

        if st.button("Run Forecast", type="primary", use_container_width=True):
            feats = build_forecast_features_for_row(city_df, idx)
            feats["city_code"] = fc_city_encoder.transform([fc_city])[0]
            X = pd.DataFrame([feats])[fc_meta["features"]]

            cols = st.columns(3)
            for i, h in enumerate([24, 48, 72]):
                pred = float(fc_models[h].predict(X)[0])
                future_idx = idx + h
                actual = city_df.loc[future_idx, "aqi"] if future_idx < len(city_df) else None
                color = aqi_to_color(pred)
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style="text-align:center; padding: 16px; border-radius: 12px; background:{color}22; border: 2px solid {color};">
                            <div style="font-size:13px; color:#555;">+{h}h Forecast</div>
                            <div style="font-size:36px; font-weight:800; color:{color};">{pred:.0f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if actual is not None:
                        st.caption(f"Actual was: **{actual:.0f}** (error: {abs(pred - actual):.1f})")

    st.markdown("---")
    st.caption("Forecast models use ONLY lag/rolling AQI history + pollutant lags + cyclic time "
               "features -- no same-timestamp pollutant readings, since those aren't available "
               "in advance in a real deployment. R² ~0.68, about 27% better than a naive "
               "'tomorrow = today' baseline across all three horizons.")

