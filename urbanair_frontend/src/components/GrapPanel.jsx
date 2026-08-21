import React from "react";

export default function GrapPanel({ data, onRefresh, refreshing }) {
  if (!data || data.length === 0) return null;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          GRAP Zone Compliance
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
            {data.length} zones · current + 24h forecast
          </span>
          {onRefresh && (
            <button onClick={onRefresh} disabled={refreshing} className="refresh-btn">
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {data.map((item) => {
          const stage = item.recommended_stage;
          return (
            <div
              key={item.point}
              style={{
                background: "var(--bg-panel-raised)",
                border: `1px solid ${item.escalation_warning ? "var(--accent)" : "var(--border-subtle)"}`,
                borderRadius: "var(--radius-md)",
                padding: "14px 16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                <strong style={{ fontSize: 14 }}>{item.point}</strong>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  {stage ? (
                    <span style={{
                      fontFamily: "var(--font-mono)", fontSize: 12, color: "#fff",
                      background: stage.color, borderRadius: 4, padding: "2px 8px",
                    }}>
                      {stage.label} · {stage.category}
                    </span>
                  ) : (
                    <span style={{
                      fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-tertiary)",
                      border: "1px solid var(--border-strong)", borderRadius: 4, padding: "2px 8px",
                    }}>
                      AQI {Math.round(item.current_aqi)} · No GRAP stage
                    </span>
                  )}
                </div>
              </div>

              {item.escalation_warning && (
                <div style={{ marginTop: 8, fontSize: 11.5, color: "var(--accent)", fontFamily: "var(--font-mono)" }}>
                  ⚠ +24h forecast crosses into {stage.label} — prepare actions before AQI arrives, don't wait.
                </div>
              )}

              {stage && (
                <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 12, color: "var(--text-secondary)" }}>
                  {stage.actions.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}