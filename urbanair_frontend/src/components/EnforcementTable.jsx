import React, { useState } from "react";
import { severityFor } from "./AqiGauge";
import AlertPanel from "./AlertPanel";

export default function EnforcementTable({ data, onRefresh, refreshing }) {
  const [expandedPoint, setExpandedPoint] = useState(null);

  if (!data || data.length === 0) return null;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          Enforcement Priority Ranking
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
            {data.length} areas · forecast + source attribution + traffic
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

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {data.map((item) => {
          const nowSev = item.current_aqi != null ? severityFor(item.current_aqi) : null;
          const fcSev = item.forecast_aqi_24h != null ? severityFor(item.forecast_aqi_24h) : null;
          const isExpanded = expandedPoint === item.point;
          return (
            <div
              key={item.point}
              style={{
                background: "var(--bg-panel-raised)",
                border: `1px solid ${item.rank <= 2 ? "var(--accent)" : "var(--border-subtle)"}`,
                borderRadius: "var(--radius-md)",
                padding: "14px 16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 12,
                      color: item.rank <= 2 ? "var(--accent)" : "var(--text-tertiary)",
                      border: `1px solid ${item.rank <= 2 ? "var(--accent)" : "var(--border-strong)"}`,
                      borderRadius: 4,
                      padding: "1px 6px",
                    }}
                  >
                    #{item.rank}
                  </span>
                  <strong style={{ fontSize: 14 }}>{item.point}</strong>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, fontWeight: 600, color: nowSev ? nowSev.color : "var(--text-secondary)" }}>
                      {item.current_aqi != null ? Math.round(item.current_aqi) : "—"}
                    </div>
                    <div style={{ fontSize: 9.5, color: "var(--text-tertiary)" }}>NOW</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 15, color: fcSev ? fcSev.color : "var(--text-secondary)" }}>
                      {item.forecast_aqi_24h != null ? Math.round(item.forecast_aqi_24h) : "—"}
                    </div>
                    <div style={{ fontSize: 9.5, color: "var(--text-tertiary)" }}>+24H</div>
                  </div>
                  <button
                    onClick={() => setExpandedPoint(isExpanded ? null : item.point)}
                    style={{
                      background: "none", border: "1px solid var(--border-strong)", borderRadius: 6,
                      color: "var(--text-secondary)", fontSize: 11, padding: "4px 10px", cursor: "pointer",
                    }}
                  >
                    {isExpanded ? "Hide alert" : "Alert"}
                  </button>
                </div>
              </div>

              {item.forecast_is_warming_up && (
                <div style={{ marginTop: 8, fontSize: 10.5, color: "var(--aqi-moderate)", fontFamily: "var(--font-mono)" }}>
                  ⚠ +24h forecast has limited confidence — this deployment is still collecting the live history the forecast model needs (see Health Advisory / Overview for details). Ranking uses whichever of NOW / +24h is worse, so priority order stays reliable either way.
                </div>
              )}

              <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-secondary)" }}>
                <strong style={{ color: "var(--text-primary)" }}>Why:</strong> {item.reasons.join(" · ")}
              </div>
              <div style={{ marginTop: 4, fontSize: 12, color: "var(--text-secondary)" }}>
                <strong style={{ color: "var(--text-primary)" }}>Action:</strong> {item.recommended_actions.join(" · ")}
              </div>

              {isExpanded && <AlertPanel point={item.point} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
