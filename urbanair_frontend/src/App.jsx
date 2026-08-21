import React, { useEffect, useState, useCallback } from "react";
import Header from "./components/Header";
import MapView from "./components/MapView";
import AqiGauge from "./components/AqiGauge";
import ForecastPanel from "./components/ForecastPanel";
import TrendChart from "./components/TrendChart";
import SourceAttributionChart from "./components/SourceAttributionChart";
import SourceAttributionCompare from "./components/SourceAttributionCompare";
import EnforcementTable from "./components/EnforcementTable";

import GrapPanel from "./components/GrapPanel";
import GrapInfoPanel from "./components/GrapInfoPanel";

import HealthAdvisoryPanel from "./components/HealthAdvisoryPanel";
import HealthAdvisoryCompare from "./components/HealthAdvisoryCompare";
import HealthAdvisoryInfoPanel from "./components/HealthAdvisoryInfoPanel";
import WhatIfPanel from "./components/WhatIfPanel";
import GreenCoverPanel from "./components/GreenCoverPanel";
import GreenCoverInfoPanel from "./components/GreenCoverInfoPanel";
import WhatIfInfoPanel from "./components/WhatIfInfoPanel";
import EnforcementInfoPanel from "./components/EnforcementInfoPanel";
import SourceAttributionInfoPanel from "./components/SourceAttributionInfoPanel";
import { api } from "./api";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "attribution", label: "Source Attribution" },
  { key: "enforcement", label: "Enforcement" },

  { key: "grap", label: "GRAP Compliance" },

  { key: "health", label: "Health Advisory" },
  { key: "whatif", label: "What-if Simulation" },
  { key: "greencover", label: "Green Cover" },
];

const ALL_POINTS = [
  "Delhi", "Faridabad", "Ghaziabad", "Gurgaon", "Noida",
  "Anand Vihar", "Ashok Vihar", "Bawana", "Dwarka", "Jahangirpuri",
  "Mundka", "Narela", "Okhla", "Punjabi Bagh", "R.K. Puram", "Rohini",
  "Vivek Vihar", "Wazirpur", "Chandni Chowk", "Red Fort", "Connaught Place",
];

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState("Delhi");
  const [cityReadings, setCityReadings] = useState([]);
  const [currentReading, setCurrentReading] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [attributionData, setAttributionData] = useState(null);
  const [attributionAllData, setAttributionAllData] = useState(null);
  const [refreshingAttribution, setRefreshingAttribution] = useState(false);
  const [attributionView, setAttributionView] = useState("single"); // "single" | "compare"
  const [whatifPoint, setWhatifPoint] = useState("Delhi");
  const [enforcementData, setEnforcementData] = useState(null);
  const [refreshingEnforcement, setRefreshingEnforcement] = useState(false);

  const [grapData, setGrapData] = useState(null);
  const [refreshingGrap, setRefreshingGrap] = useState(false);

  const [healthData, setHealthData] = useState(null);
  const [healthAllData, setHealthAllData] = useState(null);
  const [refreshingHealth, setRefreshingHealth] = useState(false);
  const [healthView, setHealthView] = useState("single"); // "single" | "compare"
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loadError, setLoadError] = useState(null);

  // Load city list + current AQI for all cities (for the map)
  const loadCities = useCallback(async () => {
    try {
      const cityList = await api.cities();
      setCities(cityList);

      // Use allSettled, not all: one city missing live data (503) shouldn't
      // take down the whole map. Cities without live data yet are simply
      // omitted from the map markers rather than shown with stale numbers.
      const results = await Promise.allSettled(
        cityList.map(async (c) => {
          const current = await api.current(c.name);
          return { ...c, aqi: current.aqi, category: current.category };
        })
      );
      const readings = results
        .filter((r) => r.status === "fulfilled")
        .map((r) => r.value);
      const failedCount = results.length - readings.length;
      if (failedCount > 0) {
        console.warn(`${failedCount} city/cities have no live data yet -- omitted from map.`);
      }
      setCityReadings(readings);
    } catch (e) {
      setLoadError("Could not reach the backend API. Is `uvicorn app.main:app` running on port 8000?");
      console.error(e);
    }
  }, []);

  useEffect(() => {
    loadCities();
  }, [loadCities]);

  // Load selected city's detail (current + forecast + historical + attribution + health)
  const loadCityDetail = useCallback(async (city) => {
    // Each call fails independently -- e.g. forecast/historical returning 503
    // during the live-data warm-up period shouldn't blank out the current
    // reading, and vice versa.
    const [current, forecast, historical, attribution, health] = await Promise.all([
      api.current(city).catch((e) => { console.error("current:", e); return null; }),
      api.forecast(city).catch((e) => { console.error("forecast:", e); return null; }),
      api.historical(city, 168).catch((e) => { console.error("historical:", e); return []; }),
      api.sourceAttribution(city).catch(() => null),
      api.healthAdvisory(city).catch(() => null),
    ]);
    setCurrentReading(current);
    setForecastData(forecast);
    setHistoricalData(historical);
    setAttributionData(attribution);
    setHealthData(health);
    setLastUpdated(new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }));
  }, []);

  useEffect(() => {
    loadCityDetail(selectedCity);
  }, [selectedCity, loadCityDetail]);

  // Load enforcement ranking once (covers all points, not city-specific)
  useEffect(() => {
    api.enforcement().then(setEnforcementData).catch((e) => console.error(e));
  }, []);

  const refreshEnforcement = useCallback(() => {
    setRefreshingEnforcement(true);
    api.enforcement()
      .then(setEnforcementData)
      .catch((e) => console.error(e))
      .finally(() => setRefreshingEnforcement(false));
  }, []);



  useEffect(() => {
  api.grapAll().then(setGrapData).catch((e) => console.error(e));
}, []);

const refreshGrap = useCallback(() => {
  setRefreshingGrap(true);
  api.grapAll().then(setGrapData).catch((e) => console.error(e)).finally(() => setRefreshingGrap(false));
}, []);


  // Load all-points attribution once, for the "compare" view
  useEffect(() => {
    api.sourceAttributionAll().then(setAttributionAllData).catch((e) => console.error(e));
  }, []);

  const refreshAttribution = useCallback(() => {
    setRefreshingAttribution(true);
    api.sourceAttributionAll()
      .then(setAttributionAllData)
      .catch((e) => console.error(e))
      .finally(() => setRefreshingAttribution(false));
  }, []);

  // Load all-points health advisory once, for the "compare" view
  useEffect(() => {
    api.healthAdvisoryAll().then(setHealthAllData).catch((e) => console.error(e));
  }, []);

  const refreshHealth = useCallback(() => {
    setRefreshingHealth(true);
    api.healthAdvisoryAll()
      .then(setHealthAllData)
      .catch((e) => console.error(e))
      .finally(() => setRefreshingHealth(false));
  }, []);

  // Auto-refresh EVERYTHING every 60s so Overview / Source Attribution /
  // Enforcement / Health Advisory / Green Cover never drift out of sync
  // with each other -- this is the single source of truth for "now".
  useEffect(() => {
    const interval = setInterval(() => {
      loadCities();
      loadCityDetail(selectedCity);
      api.enforcement().then(setEnforcementData).catch((e) => console.error(e));
      api.sourceAttributionAll().then(setAttributionAllData).catch((e) => console.error(e));
      api.healthAdvisoryAll().then(setHealthAllData).catch((e) => console.error(e));
      api.grapAll().then(setGrapData).catch((e) => console.error(e));
    }, 60000);
    return () => clearInterval(interval);
  }, [loadCities, loadCityDetail, selectedCity]);

  if (loadError) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: 12 }}>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 18 }}>Backend not reachable</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--text-secondary)", textAlign: "center", maxWidth: 420 }}>
          {loadError}
        </span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <Header cities={cities} selectedCity={selectedCity} onCityChange={setSelectedCity} lastUpdated={lastUpdated} />

      {/* Tab navigation */}
      <div style={{ display: "flex", gap: 4, padding: "10px 16px 0 16px", borderBottom: "1px solid var(--border-subtle)" }}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              background: "none",
              border: "none",
              borderBottom: activeTab === tab.key ? "2px solid var(--accent)" : "2px solid transparent",
              color: activeTab === tab.key ? "var(--accent)" : "var(--text-secondary)",
              padding: "8px 14px",
              fontSize: 13,
              fontFamily: "var(--font-body)",
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: "1fr 360px",
            gridTemplateRows: "1fr 260px",
            gridTemplateAreas: `"map side" "trend side"`,
            gap: 16,
            padding: 16,
            overflow: "hidden",
          }}
        >
          {/* Map — main visual weight */}
          <div style={{ gridArea: "map" }}>
            <MapView cityReadings={cityReadings} selectedCity={selectedCity} onSelectCity={setSelectedCity} />
          </div>

          {/* Right panel: current AQI gauge + forecast */}
          <div
            style={{
              gridArea: "side",
              background: "var(--bg-panel)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: 20,
              display: "flex",
              flexDirection: "column",
              gap: 20,
              overflowY: "auto",
            }}
          >
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-tertiary)", marginBottom: 12, letterSpacing: 0.5 }}>
                CURRENT · {selectedCity.toUpperCase()}
              </div>
              {currentReading && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <AqiGauge
                    aqi={currentReading.aqi}
                    category={currentReading.category}
                    subtitle={new Date(currentReading.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                  />
                  {currentReading.arbitration?.arbitrated && (
                    <div
                      title={currentReading.arbitration.reasoning}
                      style={{
                        marginTop: 8,
                        fontFamily: "var(--font-mono)",
                        fontSize: 10,
                        color: "var(--text-tertiary)",
                        textAlign: "center",
                        maxWidth: 200,
                      }}
                    >
                      ⓘ WAQI & model disagreed — Groq picked <b>{currentReading.arbitration.chosen}</b>
                    </div>
                  )}
                </div>
              )}
            </div>

            {currentReading?.pollutants && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                {Object.entries(currentReading.pollutants).map(([key, val]) => (
                  <div key={key} style={{ textAlign: "center", background: "var(--bg-panel-raised)", borderRadius: "var(--radius-sm)", padding: "8px 4px" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--text-primary)" }}>
                      {val != null ? val.toFixed(1) : "—"}
                    </div>
                    <div style={{ fontSize: 10, color: "var(--text-tertiary)", textTransform: "uppercase", marginTop: 2 }}>{key}</div>
                  </div>
                ))}
              </div>
            )}

            {forecastData && <ForecastPanel forecasts={forecastData.forecasts} metrics={forecastData.model_metrics} dataMaturity={forecastData.data_maturity} />}
          </div>

          {/* Bottom-left: historical trend, under the map */}
          <div
            style={{
              gridArea: "trend",
              background: "var(--bg-panel)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: 20,
            }}
          >
            <TrendChart data={historicalData} />
          </div>
        </div>
      )}

      {activeTab === "attribution" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button
              onClick={() => setAttributionView("single")}
              style={{
                background: attributionView === "single" ? "var(--accent)" : "var(--bg-panel-raised)",
                color: attributionView === "single" ? "var(--bg-base)" : "var(--text-secondary)",
                border: "none", borderRadius: "var(--radius-sm)", padding: "6px 14px", fontSize: 12, cursor: "pointer",
              }}
            >
              Single location
            </button>
            <button
              onClick={() => setAttributionView("compare")}
              style={{
                background: attributionView === "compare" ? "var(--accent)" : "var(--bg-panel-raised)",
                color: attributionView === "compare" ? "var(--bg-base)" : "var(--text-secondary)",
                border: "none", borderRadius: "var(--radius-sm)", padding: "6px 14px", fontSize: 12, cursor: "pointer",
              }}
            >
              Compare all locations
            </button>
          </div>

          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, maxWidth: attributionView === "compare" ? 700 : 520, flex: "1 1 auto" }}>
              {attributionView === "single" ? (
                attributionData ? (
                  <SourceAttributionChart data={attributionData} />
                ) : (
                  <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>
                    No traffic/weather logs found yet. Run traffic_collector.py and weather_collector.py first.
                  </span>
                )
              ) : attributionAllData ? (
                <SourceAttributionCompare data={attributionAllData} onRefresh={refreshAttribution} refreshing={refreshingAttribution} />
              ) : (
                <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>Loading comparison...</span>
              )}
            </div>
            <SourceAttributionInfoPanel />
          </div>
        </div>
      )}

      {activeTab === "enforcement" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, maxWidth: 700, flex: "1 1 auto" }}>
              {enforcementData ? (
                <EnforcementTable data={enforcementData} onRefresh={refreshEnforcement} refreshing={refreshingEnforcement} />
              ) : (
                <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>Loading enforcement ranking...</span>
              )}
            </div>
            <EnforcementInfoPanel />
          </div>
        </div>
      )}

      {activeTab === "grap" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, flex: "1 1 auto", maxWidth: 700 }}>
              <GrapPanel data={grapData} onRefresh={refreshGrap} refreshing={refreshingGrap} />
            </div>
            <GrapInfoPanel />
          </div>
        </div>
      )}


      {activeTab === "health" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button
              onClick={() => setHealthView("single")}
              style={{
                background: healthView === "single" ? "var(--accent)" : "var(--bg-panel-raised)",
                color: healthView === "single" ? "var(--bg-base)" : "var(--text-secondary)",
                border: "none", borderRadius: "var(--radius-sm)", padding: "6px 14px", fontSize: 12, cursor: "pointer",
              }}
            >
              Single location
            </button>
            <button
              onClick={() => setHealthView("compare")}
              style={{
                background: healthView === "compare" ? "var(--accent)" : "var(--bg-panel-raised)",
                color: healthView === "compare" ? "var(--bg-base)" : "var(--text-secondary)",
                border: "none", borderRadius: "var(--radius-sm)", padding: "6px 14px", fontSize: 12, cursor: "pointer",
              }}
            >
              Compare all areas
            </button>
          </div>

          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, maxWidth: healthView === "compare" ? 700 : 480, flex: "1 1 auto" }}>
              {healthView === "single" ? (
                healthData ? (
                  <HealthAdvisoryPanel data={healthData} />
                ) : (
                  <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>Loading health advisory...</span>
                )
              ) : healthAllData ? (
                <HealthAdvisoryCompare data={healthAllData} onRefresh={refreshHealth} refreshing={refreshingHealth} />
              ) : (
                <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>Loading comparison...</span>
              )}
            </div>
            <HealthAdvisoryInfoPanel />
          </div>
        </div>
      )}

      {activeTab === "whatif" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, maxWidth: 480, flex: "1 1 auto" }}>
              <WhatIfPanel points={ALL_POINTS} selectedPoint={whatifPoint} onSelectPoint={setWhatifPoint} />
            </div>
            <WhatIfInfoPanel />
          </div>
        </div>
      )}

      {activeTab === "greencover" && (
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 20, maxWidth: 700, flex: "1 1 auto" }}>
              <GreenCoverPanel />
            </div>
            <GreenCoverInfoPanel />
          </div>
        </div>
      )}
    </div>
  );
}
