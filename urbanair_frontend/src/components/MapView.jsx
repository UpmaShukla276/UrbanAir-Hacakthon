import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup, GeoJSON, useMapEvents, useMap } from "react-leaflet";
import { severityFor } from "./AqiGauge";
import { api } from "../api";
import SearchBar from "./SearchBar";

const LAYER_OPTIONS = [
  { key: "parks", label: "Parks", color: "#2DD9C0" },
  { key: "industrial", label: "Industrial zones", color: "#D9534F" },
  { key: "construction", label: "Construction sites", color: "#FFC107" },
  { key: "residential", label: "Residential", color: "#5B8DEF" },
  { key: "roads", label: "Major roads", color: "#8B96A5" },
];

const SOURCE_DISPLAY_NAMES = {
  traffic_pct: "Traffic",
  industrial_pct: "Industrial",
  construction_pct: "Construction",
  waste_burning_pct: "Waste Burning",
  background_pct: "Regional Background",
};

function ClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function FlyToLocation({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.flyTo([target.lat, target.lon], 13, { duration: 0.8 });
    }
  }, [target, map]);
  return null;
}

export default function MapView({ cityReadings, selectedCity, onSelectCity }) {
  const [activeLayers, setActiveLayers] = useState({});
  const [layerData, setLayerData] = useState({});
  const [probePoint, setProbePoint] = useState(null); // { lat, lon, name? }
  const [probeData, setProbeData] = useState(null);
  const [probeLoading, setProbeLoading] = useState(false);
  const [flyTarget, setFlyTarget] = useState(null);

  const toggleLayer = async (key) => {
    const isActive = !activeLayers[key];
    setActiveLayers((prev) => ({ ...prev, [key]: isActive }));

    if (isActive && !layerData[key]) {
      try {
        const data = await api.geojson(key);
        setLayerData((prev) => ({ ...prev, [key]: data }));
      } catch (e) {
        console.error(`Failed to load layer ${key}`, e);
      }
    }
  };

  const probeLocation = async (lat, lon, name) => {
    setProbePoint({ lat, lon, name });
    setProbeLoading(true);
    setProbeData(null);
    try {
      const data = await api.estimate(lat, lon);
      setProbeData(data);
    } catch (e) {
      console.error("Estimate failed", e);
    } finally {
      setProbeLoading(false);
    }
  };

  const handleSearchSelect = (result) => {
    setFlyTarget(result);
    probeLocation(result.lat, result.lon, result.name.split(",")[0]);
  };

  return (
    <div style={{ position: "relative", height: "100%", borderRadius: "var(--radius-lg)", overflow: "hidden", border: "1px solid var(--border-subtle)" }}>
      <MapContainer
        center={[28.6139, 77.209]}
        zoom={10}
        style={{ height: "100%", width: "100%", background: "var(--bg-base)" }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
        />

        <ClickHandler onMapClick={(lat, lon) => probeLocation(lat, lon, null)} />
        <FlyToLocation target={flyTarget} />

        {LAYER_OPTIONS.map(
          (layer) =>
            activeLayers[layer.key] &&
            layerData[layer.key] && (
              <GeoJSON
                key={layer.key}
                data={layerData[layer.key]}
                style={{ color: layer.color, weight: 1, fillOpacity: 0.15, opacity: 0.6 }}
              />
            )
        )}

        {cityReadings.map((r) => {
          const sev = severityFor(r.aqi);
          const isSelected = r.city === selectedCity;
          return (
            <CircleMarker
              key={r.city}
              center={[r.lat, r.lon]}
              radius={isSelected ? 16 : 12}
              pathOptions={{
                color: isSelected ? "var(--accent)" : sev.color,
                weight: isSelected ? 3 : 1.5,
                fillColor: sev.color,
                fillOpacity: 0.85,
              }}
              eventHandlers={{
                click: () => {
                  onSelectCity(r.city);
                  probeLocation(r.lat, r.lon, r.city);
                },
              }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>
                  <strong>{r.city}</strong>
                  <br />
                  AQI {Math.round(r.aqi)} · {r.category}
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}

        {probePoint && (
          <CircleMarker
            center={[probePoint.lat, probePoint.lon]}
            radius={9}
            pathOptions={{ color: "var(--accent)", weight: 2, fillColor: "var(--accent)", fillOpacity: 0.6, dashArray: "3,3" }}
          >
            <Popup autoPan={true} minWidth={260}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, minWidth: 240 }}>
                {probeLoading && <span>Estimating...</span>}
                {probeData && (
                  <>
                    <strong style={{ fontSize: 14 }}>{probePoint.name || "Selected point"}</strong>
                    <div style={{ margin: "8px 0", fontSize: 15 }}>
                      AQI <strong style={{ color: probeData.color }}>{Math.round(probeData.aqi)}</strong> · {probeData.category}
                    </div>
                    <div style={{ fontSize: 10, color: "#666", marginBottom: 8 }}>{probeData.proxy_note}</div>

                    {probeData.source_attribution && (
                      <div style={{ marginTop: 8, borderTop: "1px solid #ddd", paddingTop: 8 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 4 }}>Pollution contributors</div>
                        {Object.entries(probeData.source_attribution.sources)
                          .sort((a, b) => b[1] - a[1])
                          .map(([k, v]) => {
                            const label = SOURCE_DISPLAY_NAMES[k] || k;
                            return (
                              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, marginBottom: 2 }}>
                                <span>{label}</span>
                                <strong>{v}%</strong>
                              </div>
                            );
                          })}
                        <div style={{ fontSize: 9.5, color: "#777", marginTop: 6, lineHeight: 1.4 }}>
                          Regional Background = pollution transported in from outside
                          this exact spot (broader NCR conditions) -- not something a
                          local action here alone can fix.
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </Popup>
          </CircleMarker>
        )}
      </MapContainer>

      {/* Search bar */}
      <div style={{ position: "absolute", top: 12, left: 12, zIndex: 1000 }}>
        <SearchBar onSelectLocation={handleSearchSelect} />
      </div>

      {/* Layer toggle panel */}
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          zIndex: 1000,
          background: "var(--bg-panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius-md)",
          padding: "10px 12px",
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <span style={{ fontSize: 10, color: "var(--text-tertiary)", fontFamily: "var(--font-mono)", letterSpacing: 0.5, marginBottom: 2 }}>
          LAYERS
        </span>
        {LAYER_OPTIONS.map((layer) => (
          <label key={layer.key} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer", color: "var(--text-secondary)" }}>
            <input
              type="checkbox"
              checked={!!activeLayers[layer.key]}
              onChange={() => toggleLayer(layer.key)}
              style={{ accentColor: layer.color }}
            />
            <span style={{ width: 8, height: 8, borderRadius: 2, background: layer.color, display: "inline-block" }} />
            {layer.label}
          </label>
        ))}
        <span style={{ fontSize: 9, color: "var(--text-tertiary)", marginTop: 4, maxWidth: 140 }}>
          Click anywhere on the map for a hyperlocal estimate
        </span>
      </div>
    </div>
  );
}
