import React from "react";
import { severityFor } from "./AqiGauge";

export default function HealthAdvisoryPanel({ data }) {
  if (!data) return null;
  const sev = severityFor(data.current_aqi);

  return (
    <div>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: "0 0 12px 0" }}>
        Health Advisory — {data.city}
      </h3>

      <div
        style={{
          background: "var(--bg-panel-raised)",
          border: `1px solid ${sev.color}44`,
          borderRadius: "var(--radius-md)",
          padding: 16,
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 24, fontWeight: 600, color: sev.color }}>
            {Math.round(data.current_aqi)}
          </span>
          <span style={{ fontSize: 13, color: sev.color }}>{data.current_category}</span>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-primary)", marginBottom: 6 }}>
          <strong>General public:</strong> {data.general_advisory}
        </div>
        <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          <strong>Sensitive groups:</strong> {data.sensitive_groups_advisory}
        </div>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", fontFamily: "var(--font-mono)", marginBottom: 8 }}>
        FORECAST ADVISORY
      </div>
      {data.forecast_is_warming_up && (
        <div style={{ fontSize: 10.5, color: "var(--aqi-moderate)", fontFamily: "var(--font-mono)", marginBottom: 8 }}>
          ⚠ Forecast has limited confidence — still collecting the live history the model needs. Current AQI above is always live and reliable.
        </div>
      )}
      <div style={{ display: "flex", gap: 8 }}>
        {data.forecast_advisories.map((f) => {
          const fsev = severityFor(f.predicted_aqi);
          return (
            <div
              key={f.horizon_hours}
              style={{
                flex: 1,
                background: "var(--bg-panel-raised)",
                borderRadius: "var(--radius-sm)",
                padding: "10px 8px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 10, color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>+{f.horizon_hours}H</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: fsev.color, fontWeight: 600 }}>
                {Math.round(f.predicted_aqi)}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{f.category}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
