

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, classification_report
from catboost import CatBoostRegressor, CatBoostClassifier
import lightgbm as lgb

DATA_PATH = "processed_aqi_data.csv"
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------
print("Loading data...")
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)
print(f"Rows: {len(df):,} | Cities: {df['location_name'].unique().tolist()}")

# ---------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------
# Cyclic encoding for time features (same trick used in Flipkart Gridlock project)
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

# Encode city
city_encoder = LabelEncoder()
df["city_code"] = city_encoder.fit_transform(df["location_name"])

FEATURES = [
    "co", "no2", "o3", "pm10", "pm25", "so2",
    "hour_sin", "hour_cos", "month_sin", "month_cos", "dow_sin", "dow_cos",
    "is_weekend", "city_code", "location_lat", "location_lon", "year"
]
TARGET_REG = "aqi"
TARGET_CLF = "aqi_category"


train_df = df[df["year"] <= 2022].copy()
test_df = df[df["year"] >= 2023].copy()
print(f"Train: {len(train_df):,} rows | Test: {len(test_df):,} rows")

X_train, y_train = train_df[FEATURES], train_df[TARGET_REG]
X_test, y_test = test_df[FEATURES], test_df[TARGET_REG]

yc_train = train_df[TARGET_CLF]
yc_test = test_df[TARGET_CLF]


results = {}

print("\nTraining CatBoost Regressor...")
cat_reg = CatBoostRegressor(
    iterations=500, learning_rate=0.05, depth=8,
    loss_function="RMSE", random_seed=42, verbose=False
)
cat_reg.fit(X_train, y_train)
pred = cat_reg.predict(X_test)
results["CatBoost"] = {
    "R2": r2_score(y_test, pred),
    "RMSE": mean_squared_error(y_test, pred) ** 0.5,
    "MAE": mean_absolute_error(y_test, pred),
}

print("Training LightGBM Regressor...")
lgb_reg = lgb.LGBMRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=8, random_state=42, verbosity=-1
)
lgb_reg.fit(X_train, y_train)
pred_lgb = lgb_reg.predict(X_test)
results["LightGBM"] = {
    "R2": r2_score(y_test, pred_lgb),
    "RMSE": mean_squared_error(y_test, pred_lgb) ** 0.5,
    "MAE": mean_absolute_error(y_test, pred_lgb),
}

print("Training Random Forest Regressor (comparison only, not deployed)...")
rf_reg = RandomForestRegressor(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
rf_reg.fit(X_train, y_train)
pred_rf = rf_reg.predict(X_test)
results["RandomForest"] = {
    "R2": r2_score(y_test, pred_rf),
    "RMSE": mean_squared_error(y_test, pred_rf) ** 0.5,
    "MAE": mean_absolute_error(y_test, pred_rf),
}

print("\n=== Regression Results (test = 2023-2024) ===")
for name, m in results.items():
    print(f"{name:15s} R2={m['R2']:.4f}  RMSE={m['RMSE']:.3f}  MAE={m['MAE']:.3f}")

print(f"\nNote: AQI is a deterministic function of pollutant sub-indices, so all models")
print("effectively learn that formula -- R2 close to 1.0 is expected here, not overfitting.")


best_model_name = "LightGBM"
best_model = lgb_reg
print(f"Deploying: {best_model_name} (best size/accuracy trade-off for deployment)")


print("\nTraining CatBoost Classifier (AQI category)...")
cat_clf = CatBoostClassifier(
    iterations=500, learning_rate=0.05, depth=8,
    random_seed=42, verbose=False
)
cat_clf.fit(X_train, yc_train)
pred_clf = cat_clf.predict(X_test)
clf_acc = accuracy_score(yc_test, pred_clf)
print(f"Classifier accuracy: {clf_acc:.4f}")
print(classification_report(yc_test, pred_clf))


joblib.dump(best_model, MODEL_DIR / "aqi_regressor.pkl", compress=3)
joblib.dump(cat_clf, MODEL_DIR / "aqi_classifier.pkl")
joblib.dump(city_encoder, MODEL_DIR / "city_encoder.pkl")

meta = {
    "features": FEATURES,
    "best_regressor": best_model_name,
    "regression_metrics": results,
    "classifier_accuracy": clf_acc,
    "cities": city_encoder.classes_.tolist(),
    "train_years": "2019-2022",
    "test_years": "2023-2024",
}
with open(MODEL_DIR / "metadata.json", "w") as f:
    json.dump(meta, f, indent=2)

print("\nSaved: models/aqi_regressor.pkl, models/aqi_classifier.pkl, models/city_encoder.pkl, models/metadata.json")
print("Done.")
