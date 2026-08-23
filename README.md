# UrbanAir AI — Full-Stack Prototype

A Delhi NCR air quality dashboard that does monitoring, forecasting, and source attribution together. It covers all seven core features from our Feature Freeze doc: Live AQI Dashboard, Source Attribution, Enforcement Intelligence, Health Advisory, GRAP Compliance, What-if Simulation, and Green Cover Index. The Gemini Chat Assistant is the one thing we didn't get to.

## Structure

- `urbanair_backend/` — FastAPI, models, rule engines, the data API
- `urbanair_frontend/` — React + Leaflet + Recharts dashboard

## Running it, start to finish

**You'll need:** Python 3.10+ and Node.js 18+. The API keys are already sitting in `.env` files (one in `aqi_model/`, one in `urbanair_backend/`), so there's nothing to sign up for just install and go.

You'll end up running **3 terminals at once**: collectors, backend, frontend. Start them in this order.

### 1. Unzip and go to the project root
```bash
unzip urbanair_full_stack.zip
cd urbanair_full_stack
```

### 2. Terminal 1 — live-data collectors (`aqi_model/`)
```bash
cd aqi_model
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python run_all.py
```
The `.env` with the API keys is already in this folder, so there's nothing else to set up. Leave this running `run_all.py` starts all four collectors (air pollution, traffic, weather, WAQI ground AQI) on a loop, and syncs whatever they produce into `urbanair_backend/` every 5 minutes. This one command replaces running each collector separately, and it also replaces the old `sync_logs.ps1`. Give it a minute or two on first start so each collector logs at least one row before you open the dashboard, until then the backend just returns a 503 for that city.

### 3. Terminal 2 — backend (`urbanair_backend/`)
```bash
cd urbanair_full_stack
cd urbanair_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8000
```
The `.env` here (email + Groq arbitration keys) is also already filled in, nothing to configure.

### 4. Terminal 3 — frontend (`urbanair_frontend/`)
```bash
cd urbanair_full_stack
cd urbanair_frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` straight to the FastAPI backend on port 8000 — see `vite.config.js` if you're curious how.

### Day to day, after the first setup
Really only Terminal 1 needs to stay running (`python run_all.py`, from inside `aqi_model/`, venv active), that's what keeps the dashboard showing live numbers. Backend and frontend can be started and stopped independently of it and each other.

## What it actually does

Seven tabs, all working off the same **21 zones**: the 5 trained cities, 13 official CAQM hotspots, and 3 landmarks:

- **Overview** — A Leaflet map on a CARTO basemap, all 21 points colored by live AQI severity, with toggleable layers for parks, industrial zones, construction sites, residential areas, and roads. There's an instrument-style AQI gauge, pollutant readings, a 24/48/72h forecast panel, and a 7-day trend chart. You're not limited to the 21 pre-set points either, search any location in the NCR, or just click anywhere on the map for a hyperlocal estimate.
- **Source Attribution** — A donut chart breaking down where the pollution at a given point is actually coming from: Traffic, Industrial, Construction, Waste-Burning, or Regional Background. It's driven by live traffic congestion, wind direction and speed, proximity to industrial/construction zones, and a seasonal stubble-burning heuristic. There's also a compare-all view that stacks all 21 points side by side.
- **Enforcement** — A ranked priority list across all 21 points, each with a plain-language reason and a recommended action, driven by forecast severity, source mix, and traffic congestion. Every row has an alert button that can generate and actually send an Official Report plus a Hinglish Public Advisory as a real email.
- **Health Advisory** — Current and forecast CPCB-band health guidance, split for the general public versus sensitive groups.
- **GRAP Compliance** — Maps live and forecast AQI directly onto the real CAQM Graded Response Action Plan stages (I–IV) and whatever's actually mandated at that stage — halting construction, banning non-essential diesel trucks, odd-even rationing, and so on. This isn't some invented severity scale we made up; it's the exact framework Delhi NCR already runs on, so officials aren't learning a second system on top of the one they already use.
- **What-if Simulation** — Sliders to simulate cutting Traffic/Industrial/Construction/Waste-Burning by some percentage, showing the before/after AQI and the % improvement.
- **Green Cover Index** — Satellite-measured tree cover against estimated population for each of the 21 areas, checked against the commonly cited 9 sq.m/person benchmark, and tied into the *Ek Ped Maa Ke Naam* national afforestation campaign.

## Screenshots

### Dashboard
![Dashboard](assets/dashboard.png)

### Source Attribution
![Source Attribution](assets/source_attribution.png)

### Enforcement Intelligence
![Enforcement](assets/enforcement.png)

### Health Advisory
![Health Advisory](assets/advisory.png)

### GRAP Compliance
![GRAP Compliance](assets/grap.png)

### What-if Simulation
![What-if Simulation](assets/what-if-simulation.png)

### Green Cover Index
![Green Cover](assets/green_cover.png)

## Design direction

We built this as a control-room instrument panel, not a marketing page, the people actually using it are DPCC/MCD officials trying to read live conditions fast. That's why it's a clean, high-contrast light base, so severity colors still jump out at a glance, monospace (IBM Plex Mono) on every numeric readout so numbers feel measured rather than decorative, and Space Grotesk for headers. The AQI severity palette carries real regulatory meaning (CPCB bands), so we kept it deliberately separate from the app's own teal accent color so nobody should ever confuse "the brand color" with "an actual pollution reading."

## How well the models actually perform

Two models here, and they're solving very different problems:

- **Nowcast** (pollutants → AQI): R² of 0.9999, 99.8% category accuracy. This one's almost expected to be near-perfect, AQI is literally a formula of pollutant sub-indices, so the model is just learning that formula, not really predicting anything.
- **Forecast** (24h/48h/72h out): R² of about 0.68 across all three horizons, and it's only trained on information that would genuinely be known ahead of time, lagged AQI and PM readings, rolling stats correctly shifted so "now" never leaks into its own window. It beats a naive "tomorrow looks like today" baseline by roughly 27% at every horizon. This is the number that actually reflects the model learning something, rather than recomputing a formula, if someone asks which result is harder, this is the one to point to, not the 0.9999.

## WAQI vs. model arbitration (Groq)

When the live ground-station reading (WAQI) and our model's own estimate disagree by more than 15%, we send both to a Groq LLM call along with some context recent trend, pollutant levels, each source's typical error pattern, and it weighs the two the way an analyst might cross-check two instruments that don't quite agree. Worth being upfront about what this is: it's a plausibility check, not verified ground truth. An LLM can't actually measure air. If the two sources already agree, none of this runs — WAQI is used directly, no API call needed. And if the Groq key is missing or the call fails for any reason, it just falls back to WAQI rather than blocking the request. See `groq_arbiter.py` if you want the details.

## A real data bug we caught

The geospatial layers we started with parks, residential, industrial, roads were quietly broken. An Overpass query got scoped wrong somewhere along the way, so `parks.geojson` and `residential.geojson` were actually mapped to **Rome, Italy**, and `industrial.geojson` and `roads.geojson` came back completely empty. We re-extracted all five layers ourselves, straight from the regional OSM PBF, clipped precisely to the same bounding box as the pollutant rasters: 283,558 roads, 12,641 major roads, 4,777 parks, 4,166 residential zones, 635 industrial zones. Details are in `extract_osm_layers.py`.

## API endpoints (backend)

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Basic healthcheck |
| `GET /api/cities` | List of 5 cities + coordinates |
| `GET /api/current/{city}` | Latest known AQI + pollutants |
| `POST /api/nowcast` | AQI from manually entered pollutant readings |
| `GET /api/forecast/{city}` | 24/48/72h forecast (optional `reference_time` for demo/backtest mode) |
| `GET /api/historical/{city}?hours=168` | Time series for the trend chart |
| `GET /api/geojson/{layer}` | `parks` \| `residential` \| `industrial` \| `construction` \| `roads` |
| `GET /api/source-attribution` | Traffic/Industrial/Construction/Waste-Burning/Background % for all 21 points, for the compare view |
| `GET /api/source-attribution/{point}` | Same, for one city or hotspot |
| `GET /api/enforcement` | Ranked priority list with reasons + recommended actions |
| `GET /api/health-advisory/{city}` | Current + forecast health advisory (CPCB-band text) |
| `GET /api/health-advisory` | Same, for all 21 monitored points at once |
| `GET /api/grap/{point}` | GRAP stage (current + 24h forecast) for one zone |
| `GET /api/grap` | Same, for all 21 zones at once |
| `POST /api/whatif` | Simulate reducing sources by X%, get before/after AQI |
| `GET /api/green-cover` | Green Cover Index for all 21 areas |
| `GET /api/green-cover/{point}` | Same, for one area |
| `GET /api/search-location?query=...` | Free-text geocoding (Nominatim), NCR-bounded |
| `GET /api/estimate?lat=..&lon=..` | Hyperlocal estimate for any point, not just the 21 pre-registered ones |
| `GET /api/alerts/officials/{point}` | Generates structured official-report analysis text |
| `GET /api/alerts/public/{point}` | Generates short Hinglish public advisory text |
| `POST /api/alerts/send` | Sends either as an email (needs SMTP configured) |
| `GET /api/alerts/status` | Whether SMTP is configured |

## Keeping traffic/weather/AQI data fresh

`source_attribution.py`, `main.py`, and `live_history.py` all read their live CSVs: `traffic_log.csv`, `weather_current_log.csv`, `live_pollutants_log.csv`, `live_ground_aqi_log.csv` ,from inside `urbanair_backend/`. But the collectors in `aqi_model/` write to `aqi_model/` instead. `run_all.py` handles copying the latest files across automatically every 5 minutes, so as long as it's running, you genuinely don't need to think about this. If numbers ever look stale, the first thing to check is whether Terminal 1 is still alive.

No backend restart is ever needed for this either way it just re-reads the CSVs fresh on every request.

## Why Source Attribution and Enforcement are rule-based, not ML

This was a deliberate choice, not a shortcut. There's no labeled "ground truth pollution source" dataset for Delhi NCR to train against and that's true of real-world source apportionment too. CPCB and SAFAR run similar rule-plus-dispersion-model hybrids themselves, not pure ML. Every weight in `source_attribution.py` is a documented assumption grounded in known atmospheric behavior like wind carries industrial and agricultural smoke, calm wind concentrates pollutants locally, stubble burning is seasonal to Oct–Nov which is not something fitted to data. It's worth saying this out loud in a demo as "explainable rule-based reasoning," honestly a stronger pitch for a government tool than a black box would be, since an official can actually audit the reasoning.

## Why 21 zones, not 5 cities

We expanded from the original 7 points to Delhi's 13 officially designated pollution hotspots: Anand Vihar, Ashok Vihar, Bawana, Dwarka, Jahangirpuri, Mundka, Narela, Okhla, Punjabi Bagh, R.K. Puram, Rohini, Vivek Vihar, Wazirpur, per the Dept. of Environment, GNCTD, 2018 — plus 3 landmark locations (Chandni Chowk, Red Fort, Connaught Place). That's 21 points total, and Source Attribution, Enforcement, GRAP Compliance, and What-if all operate at this level now, not just city level. The coordinates are approximate locality centroids, so if you need CAAQMS-station-grade precision, cross-check against CPCB's official station list, there's a link in `source_attribution.py`'s comments.

## Email alerts

Already configured in the included `.env`, so there's nothing to set up — just restart the backend to pick it up. Without SMTP credentials, alert *preview* still works completely fine; only actually sending needs them. `GET /api/alerts/status` will tell you whether it's configured.

Worth being clear about this: it's a demo-grade email sender, not a government notification system. A real deployment would swap this out for whatever official channel DPCC/MCD actually uses SMS gateway, an internal alert queue, WhatsApp Business API, whatever it is. Say that explicitly if it comes up in a demo; don't let it come across as production-ready infrastructure, because it isn't.

## What's still left

- **Gemini Chat Assistant** — Wrapping the existing endpoints' outputs as context for a Gemini call, so someone could ask something like "why is AQI increasing in Anand Vihar" and get an answer built from the attribution and forecast data we've already computed. This is genuinely the fastest thing left to build, since all the underlying data is already there.

## Things worth saying honestly

These also show up in every relevant API response's `caveats` or `disclaimer` field, and in the UI itself:

- Green Cover's population figures are district-density estimates, not exact ward-level census counts. Real ward-level data would need an MCD ward shapefile plus a matching table, and that's not easy to get publicly.
- The "trees needed" number is illustrative, area deficit divided by average mature-tree canopy size, not a literal planting order. Actual reforestation planning needs species selection, site surveys, all of that.
- The 9 sq.m/person figure is a commonly cited planning reference in urban literature, but it doesn't trace back to one single official WHO document. Treat it as a benchmark, not a regulatory mandate.
- What-if Simulation is a rough linear-scaling estimate for comparing scenarios, not a validated dispersion-model simulation. It's good for figuring out which lever matters more, not for engineering-grade prediction. We don't include population-impact estimates since we don't have ward-level census data and if someone asks for that number, don't make it up, just say it needs that data source.

If real ward-level population data ever becomes available (Census or MCD), the `POPULATION_DENSITY` dict in `green_cover.py` is the only thing that needs replacing and the rest of the pipeline stays as is.

## Regenerating the tree-cover raster

`gee_tree_cover_extraction.js` (in `aqi_model/`) is the Google Earth Engine script that generated `DelhiNCR_TreeCover_2021.tif`. Re-run it in the GEE Code Editor if you need a different year, radius, or region.
