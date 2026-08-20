import React from "react";
import { severityFor } from "./AqiGauge";

const ACTION_CHIP = {
  Good: { label: "Outdoor activity OK", tone: "var(--aqi-good)" },
  Satisfactory: { label: "Outdoor activity OK", tone: "var(--aqi-satisfactory)" },
  Moderate: { label: "Sensitive groups: reduce exertion", tone: "var(--aqi-moderate)" },
  Poor: { label: "Mask advised outdoors", tone: "var(--aqi-poor)" },
  "Very Poor": { label: "Avoid outdoor activity", tone: "var(--aqi-very-poor)" },
  Severe: { label: "Stay indoors", tone: "var(--aqi-severe)" },
};

const summaryBoxStyle = {
  flex: 1,
  background: "var(--bg-panel-raised)",
  borderRadius: "var(--radius-md)",
  padding: "12px 14px",
  textAlign: "center",
};

export default function HealthAdvisoryCompare({ data, onRefresh, refreshing }) {
  if (!data || data.length === 0) return null;

  const sorted = [...data].sort((a, b) => b.current_aqi - a.current_aqi);
  const worst = sorted[0];
  const concernCount = data.filter((d) =>
    ["Very Poor", "Severe"].includes(d.current_category)
  ).length;
  const worstSev = severityFor(worst.current_aqi);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          Health Advisory — All Areas
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
            {data.length} areas
          </span>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className="refresh-btn"
            >
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          )}
        </div>
      </div>
      <p style={{ fontSize: 11, color: "var(--text-tertiary)", margin: "6px 0 16px 0", lineHeight: 1.5 }}>
        Public-facing guidance for all 21 monitored points. The 5 trained cities use
        live sensor/model readings; the other 16 points are proxied from the nearest
        trained city (labeled on each card) since they don't have a live sensor of
        their own.
      </p>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div style={summaryBoxStyle}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 600, color: concernCount > 0 ? "var(--aqi-poor)" : "var(--aqi-good)" }}>
            {concernCount}/{data.length}
          </div>
          <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>areas Very Poor or worse</div>
        </div>
        <div style={summaryBoxStyle}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600, color: worstSev.color }}>
            {worst.point}
          </div>
          <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>
            most affected right now ({Math.round(worst.current_aqi)} AQI)
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {sorted.map((d) => {
          const sev = severityFor(d.current_aqi);
          const chip = ACTION_CHIP[d.current_category] ?? ACTION_CHIP["Moderate"];
          return (
            <div
              key={d.point}
              style={{
                background: "var(--bg-panel-raised)",
                border: `1px solid ${sev.color}33`,
                borderRadius: "var(--radius-md)",
                padding: "12px 14px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, gap: 8 }}>
                <div>
                  <strong style={{ fontSize: 13 }}>{d.point}</strong>
                  {!d.is_directly_measured && (
                    <div style={{ fontSize: 10, color: "var(--text-tertiary)", fontFamily: "var(--font-mono)", marginTop: 2 }}>
                      est. from {d.nearest_known_city} · {d.distance_to_nearest_city_km} km away
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 6, flexShrink: 0 }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 18, fontWeight: 600, color: sev.color }}>
                    {Math.round(d.current_aqi)}
                  </span>
                  <span style={{ fontSize: 11, color: sev.color }}>{d.current_category}</span>
                </div>
              </div>

              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 10, lineHeight: 1.5 }}>
                {d.general_advisory}
              </div>

              <span
                style={{
                  fontSize: 10, padding: "3px 9px", borderRadius: 20,
                  border: `1px solid ${chip.tone}`, color: chip.tone,
                  fontFamily: "var(--font-mono)", display: "inline-block",
                }}
              >
                {chip.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
