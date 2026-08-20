# UrbanAir AI — Full-Stack Prototype

Delhi NCR air quality monitoring + forecasting + source-attribution
dashboard. Covers Features 1, 2, 3, 4, 5 from the Feature Freeze doc
(Live AQI Dashboard, Hyperlocal Forecast, Source Attribution, Enforcement
Intelligence, Health Advisory). Only the Gemini Chat Assistant and the
What-if Simulation stretch goal remain.

## Structure

```
urbanair_backend/     ← FastAPI (models + rule engines + data API)
urbanair_frontend/    ← React + Leaflet + Recharts dashboard
```

## Run it (full setup, start to end)

**Prerequisites:** Python 3.10+ and Node.js 18+. API keys are already
included in `.env` (aqi_model/) and `.env` (urbanair_backend/) — nothing
to sign up for, just install and run.

You'll end up with **3 terminals running at once** — collectors, backend,
frontend. Start them in this order.

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
`.env` with the API keys is already in this folder — no setup needed
there. Leave this running. `run_all.py` starts all 4 collectors (air
pollution, traffic, weather, WAQI ground AQI) on loop, **and** syncs the
logs it produces into `urbanair_backend/` every 5 minutes automatically —
this single command replaces running each collector separately and the
old `sync_logs.ps1`. Give it a minute or two after first starting so each
collector has logged at least one row before you open the dashboard —
the backend returns a 503 for a city until its first live reading lands.

### 3. Terminal 2 — backend (`urbanair_backend/`)
```bash
cd urbanair_full_stack
cd urbanair_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8000
```
`.env` (email + Groq arbitration keys) is already included here too —
nothing else to configure.

### 4. Terminal 3 — frontend (`urbanair_frontend/`)
```bash
cd urbanair_full_stack
cd urbanair_frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the Vite dev server proxies `/api/*` to
the FastAPI backend on port 8000 automatically (see `vite.config.js`).

### Day-to-day after first setup
Only Terminal 1 (`python run_all.py`, from inside `aqi_model/` with its
venv active) needs to be kept running for fresh data — leave it up
whenever you want the dashboard showing live numbers. Backend and
frontend can be started/stopped independently of it.

## What it does

Four tabs:

- **Overview** — Map (Leaflet, dark CARTO basemap) with 5 city markers
  colored by live AQI severity, toggleable layers (parks/industrial/
  construction/residential/roads), instrument-style AQI gauge, pollutant
  readings, 24/48/72h forecast panel, 7-day trend chart.
- **Source Attribution** — donut chart breaking down Traffic / Industrial
  / Construction / Waste-Burning / Regional Background % for the
  selected city, using live traffic congestion + wind direction/speed +
  proximity to industrial/construction zones + a seasonal stubble-burning
  heuristic.
- **Enforcement** — ranked priority list across all monitored points
  (5 cities + Anand Vihar + Rohini hotspots), each with plain-language
  reasons and recommended actions, driven by forecast severity + source
  mix + traffic congestion.
- **Health Advisory** — current + forecast CPCB-band health advisory
  text for general public and sensitive groups.


##  Application Screenshots

### Dashboard
![Dashboard](assets/dashboard.png)

### Source Attribution
![Source Attribution](assets/source_attribution.png)

### Enforcement Intelligence
![Enforcement](assets/enforcement.png)

### Health Advisory
![Health Advisory](assets/advisory.png)

### Green Cover Index
![Green Cover](assets/green_cover.png)

### What-if Simulation
![What-if Simulation](assets/what-if-simulation.png)

## Design direction

Built as a control-room / instrumentation interface (not a marketing
page) since the actual audience is DPCC/MCD officials monitoring live
conditions: dark base so severity colors read clearly, monospace
(IBM Plex Mono) for all numeric readouts to feel measured, Space Grotesk
for headers. The AQI severity palette carries real meaning (CPCB bands),
kept separate from the app's own accent color (teal) so users never
confuse "the brand color" with "a pollution reading."

## API endpoints (backend)

| Endpoint | Purpose |
|---|---|
| `GET /api/cities` | List of 5 cities + coordinates |
| `GET /api/current/{city}` | Latest known AQI + pollutants |
| `POST /api/nowcast` | AQI from manually entered pollutant readings |
| `GET /api/forecast/{city}` | 24/48/72h forecast (optional `reference_time` for demo/backtest mode) |
| `GET /api/historical/{city}?hours=168` | Time series for the trend chart |
| `GET /api/geojson/{layer}` | `parks` \| `residential` \| `industrial` \| `construction` \| `roads` |
| `GET /api/source-attribution` | Traffic/Industrial/Construction/Waste-Burning/Background % for all points |
| `GET /api/source-attribution/{point}` | Same, for one city or hotspot |
| `GET /api/enforcement` | Ranked priority list with reasons + recommended actions |
| `GET /api/health-advisory/{city}` | Current + forecast health advisory (CPCB-band text) |

## Keeping traffic/weather/AQI data fresh

`source_attribution.py`, `main.py`, and `live_history.py` all read their
live CSVs (`traffic_log.csv`, `weather_current_log.csv`,
`live_pollutants_log.csv`, `live_ground_aqi_log.csv`) **from inside
`urbanair_backend/`**, but the collectors in `aqi_model/` write to
`aqi_model/` instead. `python run_all.py` (see setup above) handles
copying the latest files across automatically every 5 minutes — as long
as it's running, you don't need to think about this. If you ever see
stale numbers, check that Terminal 1 (`run_all.py`) is still alive.

No backend restart is needed either way — it re-reads the CSVs on every
request.

## Important note on Source Attribution / Enforcement

These are **transparent rule-based engines**, not trained ML classifiers
-- there's no labeled "ground truth pollution source" dataset to train
against (this is true of real-world source apportionment too; CPCB/SAFAR
use similar rule + dispersion-model hybrids, not pure ML). Every weight
in `source_attribution.py` is a documented assumption based on known
atmospheric behavior (wind carries industrial/agricultural smoke, calm
wind concentrates pollutants, stubble burning is seasonal Oct-Nov), not a
fitted parameter. This is honest to present in your report/demo as
"explainable rule-based reasoning" -- arguably a stronger pitch for a
government-facing tool than an opaque model would be.

## Recent additions (v3)

- **Area-wise granularity**: expanded from 7 points to Delhi's **13
  officially designated pollution hotspots** (Anand Vihar, Ashok Vihar,
  Bawana, Dwarka, Jahangirpuri, Mundka, Narela, Okhla, Punjabi Bagh,
  R.K. Puram, Rohini, Vivek Vihar, Wazirpur -- per Dept. of Environment,
  GNCTD, 2018) plus 3 iconic landmarks (Chandni Chowk, Red Fort,
  Connaught Place). Source Attribution, Enforcement, and What-if now all
  work at this area level, not just city level. Coordinates are
  approximate locality centroids -- cross-check against CPCB's official
  CAAQMS station list if you need monitoring-station-grade precision
  (link is in `source_attribution.py`'s comments).
- **Alert generation + sending**: each row in the Enforcement tab has an
  "Alert" button that expands to show two previews -- an **Official
  Report** (structured analysis: AQI, forecast, source breakdown, why
  flagged, recommended actions) and a **Public Advisory** (short,
  Hinglish, actionable message). Both can be sent as a real email via
  `/api/alerts/send`.

### Email alerts

Already configured in the included `.env` — no setup needed.

Restart the backend. Without this, alert *preview* still works fully --
only actual sending needs the SMTP credentials. `GET /api/alerts/status`
tells you if it's configured.

**This is a demo-grade email sender, not a government notification
system.** A real deployment would replace this with whatever official
channel DPCC/MCD uses (SMS gateway, internal alert queue, WhatsApp
Business API, etc.) -- say this explicitly if asked in the demo, don't
imply this is production-ready infrastructure.

### New endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/alerts/officials/{point}` | Generates structured analysis report text |
| `GET /api/alerts/public/{point}` | Generates short public advisory text |
| `POST /api/alerts/send` | Sends either as an email (needs SMTP configured) |
| `GET /api/alerts/status` | Whether SMTP is configured |

## What's left

- **Gemini Chat Assistant** — wrap the above endpoints' outputs as
  context for a Gemini API call, answering questions like "why is AQI
  increasing in Anand Vihar" using the already-computed attribution +
  forecast data. This is the fastest remaining feature to build since
  all the underlying data is ready.

## Recent additions (v4) — Green Cover Index

Ties to the **Ek Ped Maa Ke Naam** (One Tree in Mother's Name) national
afforestation campaign. For each of the 21 areas:

- **Tree cover %** from ESA WorldCover 10m satellite data (2021, free,
  via Google Earth Engine) within a 2km radius
- **Estimated population** from Census 2011 district-level density
  (see `green_cover.py`'s `POPULATION_DENSITY` table for exactly which
  district was assigned to each area, and why)
- **Green sq.m per capita** vs. the widely-cited 9 sq.m/person planning
  benchmark
- **Illustrative tree count needed** to close the gap

**Important honesty notes** (also returned in every API response's
`caveats` field, and shown in the UI):
- Population figures are district-density estimates, not exact ward
  census counts -- ward-level population data would need an MCD ward
  shapefile + matching table, which isn't publicly easy to source.
- The "trees needed" number is illustrative (area deficit ÷ average
  mature-tree canopy size), not a literal planting order -- actual
  reforestation planning needs species selection, site surveys, etc.
- The 9 sq.m/person figure is a commonly cited planning reference in
  urban literature, but isn't traceable to one single official WHO
  document -- treat it as a benchmark, not a regulatory mandate.

If you get access to real ward-level population data (Census or MCD),
replace the `POPULATION_DENSITY` dict in `green_cover.py` with an actual
per-area lookup -- the rest of the pipeline doesn't need to change.

### New endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/green-cover` | Green Cover Index for all 21 areas |
| `GET /api/green-cover/{point}` | Same, for one area |

### Regenerating the tree-cover raster

`gee_tree_cover_extraction.js` (in `aqi_model/`) is the Google Earth
Engine script used to generate `DelhiNCR_TreeCover_2021.tif`. Re-run it
in the GEE Code Editor if you need a different year, radius, or region.

## Recent additions (v2)

- **Fixed date bug**: the AQI gauge was showing "01 Jan, 12:00 am"
  because `/api/current` returned the historical dataset's last row
  timestamp (which ends Jan 2024). Now shows the real current time, with
  a small "est. from last known reading (01 Jan 2024)" note for honesty
  about the data source.
- **Search any location** — a search bar (top-left of the map) using free
  OpenStreetMap Nominatim geocoding, restricted to the Delhi NCR bbox.
  Type any place name, click a result, map flies there and shows an
  estimate.
- **Click anywhere on the map** — same estimate popup, for any point you
  click, not just the 5 pre-registered cities. AQI/forecast are proxied
  from the nearest trained city (labeled honestly), but **Source
  Attribution is computed fresh** for the exact clicked point using the
  static geospatial layers + nearest live traffic/weather -- this part is
  genuinely hyperlocal.
- **Compare-all view** in the Source Attribution tab — a stacked bar
  chart showing Traffic/Industrial/Construction/Waste-Burning/Background
  % side-by-side for all 7 monitored points at once, so you can see at a
  glance which location has which dominant source (e.g. Anand Vihar's
  industrial contribution stands out clearly against the other points).
- **What-if Simulation tab** — sliders to simulate reducing
  Traffic/Industrial/Construction/Waste-Burning by X%, shows before/after
  AQI and % improvement. Method: splits current AQI into a "background"
  floor (not locally controllable) and a "local" component distributed
  across sources per their attribution %, then applies the requested
  reduction to each slice. This is a rough linear-scaling estimate for
  scenario comparison, not a validated dispersion-model simulation --
  documented clearly in the API response's `disclaimer` field and worth
  saying out loud in your demo too. Population-impact estimates aren't
  included since we don't have ward-level census data -- don't fabricate
  that number if asked; say it needs that data source.

### New endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/search-location?query=...` | Free-text geocoding (Nominatim), NCR-bounded |
| `GET /api/estimate?lat=..&lon=..` | Hyperlocal estimate for ANY point (not just the 5 cities) |
| `POST /api/whatif` | Simulate reducing sources by X%, get before/after AQI |
| `GET /api/source-attribution` (no path param) | All 7 points at once, for the compare view |
