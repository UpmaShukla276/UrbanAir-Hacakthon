import React from "react";
import { severityFor } from "./AqiGauge";

export default function ForecastPanel({ forecasts, metrics, dataMaturity }) {
  if (!forecasts || forecasts.length === 0) return null;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0, color: "var(--text-primary)" }}>
          Forecast
        </h3>
      </div>

      {dataMaturity?.is_warming_up && (
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 10,
            color: "var(--aqi-moderate)",
            background: "var(--bg-panel-raised)",
            border: "1px solid var(--aqi-moderate)33",
            borderRadius: "var(--radius-sm)",
            padding: "6px 8px",
            marginBottom: 10,
          }}
        >
          ⚠ Collecting live history: {dataMaturity.hours_available}h / {dataMaturity.hours_needed_for_full_accuracy}h needed.
          Forecast accuracy improves as more live data comes in.
        </div>
      )}

      <div style={{ display: "flex", gap: 10 }}>
        {forecasts.map((f) => {
          const sev = severityFor(f.predicted_aqi);
          const m = metrics?.[`${f.horizon_hours}h`];
          return (
            <div
              key={f.horizon_hours}
              style={{
                flex: 1,
                background: "var(--bg-panel-raised)",
                border: `1px solid ${sev.color}33`,
                borderRadius: "var(--radius-md)",
                padding: "14px 10px",
                textAlign: "center",
              }}
            >
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-tertiary)", marginBottom: 6 }}>
                +{f.horizon_hours}H
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 28, fontWeight: 600, color: sev.color, lineHeight: 1 }}>
                {Math.round(f.predicted_aqi)}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 6 }}>
                {f.predicted_category}
              </div>
              {m && (
                <div style={{ fontSize: 9, color: "var(--text-tertiary)", marginTop: 6, fontFamily: "var(--font-mono)" }}>
                  R² {m.R2.toFixed(2)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}