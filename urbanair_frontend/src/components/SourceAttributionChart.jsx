import React from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const SOURCE_COLORS = {
  traffic_pct: "#FF7A00",
  industrial_pct: "#D9534F",
  construction_pct: "#8B96A5",
  waste_burning_pct: "#FFC107",
  background_pct: "#2DD9C0",
};

const SOURCE_LABELS = {
  traffic_pct: "Traffic",
  industrial_pct: "Industrial",
  construction_pct: "Construction",
  waste_burning_pct: "Waste Burning",
  background_pct: "Regional Background",
};

export default function SourceAttributionChart({ data }) {
  if (!data) return null;

  const chartData = Object.entries(data.sources).map(([key, value]) => ({
    key,
    name: SOURCE_LABELS[key],
    value,
    color: SOURCE_COLORS[key],
  }));

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          Source Attribution — {data.point}
        </h3>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
          rule-based · explainable
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <ResponsiveContainer width={180} height={180}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={45}
              outerRadius={80}
              paddingAngle={2}
            >
              {chartData.map((entry) => (
                <Cell key={entry.key} fill={entry.color} stroke="var(--bg-panel)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "var(--bg-panel-raised)", border: "1px solid var(--border-strong)", borderRadius: 8, fontFamily: "var(--font-mono)", fontSize: 12 }}
              formatter={(value) => `${value}%`}
            />
          </PieChart>
        </ResponsiveContainer>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
          {chartData
            .sort((a, b) => b.value - a.value)
            .map((entry) => (
              <div key={entry.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 13 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 10, height: 10, borderRadius: 3, background: entry.color, display: "inline-block" }} />
                  <span style={{ color: "var(--text-secondary)" }}>{entry.name}</span>
                </div>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{entry.value}%</span>
              </div>
            ))}
        </div>
      </div>

      <div style={{ marginTop: 12, padding: "8px 12px", background: "var(--bg-panel-raised)", borderRadius: 8, fontSize: 11, color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
        Wind {data.raw_signals.wind_speed_mps} m/s @ {data.raw_signals.wind_deg}° · Congestion ratio {data.raw_signals.congestion_ratio}
        {data.raw_signals.is_stubble_burning_season && " · Stubble-burning season active"}
      </div>
    </div>
  );
}
