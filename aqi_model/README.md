# AQI Prediction Model — Delhi NCR

Predicts Air Quality Index (value + category) from pollutant concentrations,
city, and time features. Trained on your `processed_aqi_data.csv`
(2019–2024, hourly, 5 NCR cities: Delhi, Faridabad, Ghaziabad, Gurgaon, Noida).

## What's inside

```
aqi_model/
├── processed_aqi_data.csv          ← historical AQI + pollutants (2019-2024)
├── raw_data/                       ← original Sentinel-5P concentration TIFs
├── delhi_ncr_*.geojson             ← CORRECTED geospatial layers (see note below)
├── ncr_grid_points.csv             ← 43 lat/lon points for traffic/weather collection
├── generate_grid_points.py         ← regenerates the grid (edit N for more/fewer points)
├── extract_osm_layers.py           ← extracts roads/parks/residential/industrial from PBF
├── traffic_collector.py            ← TomTom collector (run repeatedly to build history)
├── weather_collector.py            ← OpenWeatherMap collector (current + 5-day forecast)
├── train_model.py                  ← trains the nowcasting AQI model
├── app.py                          ← Streamlit app for live predictions
├── requirements.txt
└── models/                         ← trained regressor + classifier
```

## ⚠️ Important data correction

Your original `parks.geojson` and `residential.geojson` were actually **Rome,
Italy** data (Overpass query was scoped wrong). `industrial.geojson` and
`roads.geojson` were empty (0 features).

Fixed by extracting directly from your `northern-zone-260709_osm.pbf`,
clipped to the exact same bbox as your concentration rasters:

| File | Count |
|---|---|
| `delhi_ncr_roads.geojson` | 283,558 (all roads incl. residential streets) |
| `delhi_ncr_major_roads.geojson` | 12,641 (motorway/trunk/primary/secondary — use this for the dashboard map, the full file is 87MB and will choke Leaflet) |
| `delhi_ncr_parks.geojson` | 4,777 |
| `delhi_ncr_residential.geojson` | 4,166 |
| `delhi_ncr_industrial.geojson` | 635 |

## Data collection — run these NOW, starting today

Both TomTom and OpenWeatherMap only give current/forecast snapshots, no
historical bulk data on free tier. Start logging immediately so you have
real multi-day time-series by submission day.

```bash
export TOMTOM_API_KEY="your_key"
export OWM_API_KEY="your_key"

# Run once to test:
python traffic_collector.py
python weather_collector.py

# Then run continuously in the background (separate terminals / screen / tmux):
python traffic_collector.py --loop 30    # every 30 min
python weather_collector.py --loop 60    # every 60 min (weather changes slower)
```

This builds `traffic_log.csv` and `weather_current_log.csv` /
`weather_forecast_log.csv` over the next few days — even 3 days of hourly
snapshots is enough to see rush-hour and day/night traffic patterns for
Source Attribution.

## Setup

```bash
pip install -r requirements.txt
```

## Train (models/ already included, but to retrain)

```bash
python train_model.py
```

## Run the app

```bash
streamlit run app.py
```

## Results (nowcasting model)

| Model | R² | RMSE | MAE |
|---|---|---|---|
| CatBoost | 0.9999 | 0.565 | 0.364 |
| **LightGBM (deployed)** | **0.9999** | **0.520** | **0.282** |
| RandomForest | 1.0000 | 0.009 | 0.004 |

Classifier (AQI category) accuracy: **99.8%**

## Important thing to understand

AQI is a **deterministic formula** applied to pollutant sub-indices, so a
model trained on pollutant concentrations → AQI essentially learns that
formula — R² near 1.0 is expected, not a data leak.

This is useful for: instant AQI computation from live sensor readings,
filling gaps where AQI is missing, and powering the dashboard's live map.

## Forecast Engine (24/48/72hr) — ✅ Done

`train_forecast_model.py` trains three separate LightGBM models (one per
horizon), using ONLY information available in advance:

- **Lag features**: AQI 1h/24h/48h/72h/168h ago, per city
- **Rolling stats**: 24h and 168h rolling mean/std/max (all correctly
  shifted so "now" never leaks into its own window)
- **Trend**: short-term rise/fall signal
- **Pollutant lags**: PM2.5/PM10 24h ago + rolling mean (these often move
  before AQI does — e.g. stubble-burning smoke arriving)
- **Cyclic time features**: hour/month/day-of-week

Deliberately **excludes** same-timestamp pollutant concentrations, since
those won't be known in advance in a real deployment — using them would
be leakage that inflates the score without being real.

### Results (test period: 2023-2024, held out)

| Horizon | R² | MAE | Naive baseline MAE | Improvement |
|---|---|---|---|---|
| 24h | 0.680 | 31.2 | 43.0 | 27.5% better |
| 48h | 0.679 | 31.2 | 42.8 | 27.1% better |
| 72h | 0.678 | 31.3 | 43.0 | 27.4% better |

"Naive baseline" = predicting the future AQI will just equal the current
AQI (a standard, honest benchmark for time-series forecasting). Beating
it by ~27% across all three horizons is a legitimate, defensible result
for your report/demo — unlike the nowcasting model's R²=0.9999 (which is
expected since AQI is a formula of pollutants), this R²=0.68 reflects
genuine predictive uncertainty, which is what forecasting should look like.

Try it live in the **Forecast tab** of `app.py` — pick a city and a past
moment from the test period, and it'll show the prediction next to what
actually happened.

## Next up

Once `traffic_log.csv` / `weather_forecast_log.csv` have a few days of
real data, next steps are:
1. **Weather correction layer** — adjust the forecast using live wind
   speed/direction, humidity from the `/forecast` endpoint
2. **Source Attribution Engine** — rule-based scoring using traffic
   congestion (from `traffic_log.csv`) + proximity to industrial/
   residential zones (from the corrected GeoJSONs) + wind direction
3. **Enforcement Intelligence** — ranks hotspots using Forecast +
   Source Attribution output
4. **Health Advisory** — simple AQI-band → advice rule table, joined to
   ward/population data
5. **FastAPI backend** wiring all of the above + **Gemini chat assistant**

Send traffic/weather logs whenever ready and we'll keep building.
