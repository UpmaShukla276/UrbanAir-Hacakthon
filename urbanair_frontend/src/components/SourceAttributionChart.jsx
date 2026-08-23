import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const SOURCE_COLORS = {
  traffic_pct: "#f5ca0b",
  industrial_pct: "#D9534F",
  construction_pct: "#798597",
  waste_burning_pct: "#f9f95a",
  background_pct: "#058bac",
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

  // Build once, sort once -- this SAME array (not a re-sorted copy) drives
  // both the Pie's slice order and the legend list below, so a slice's
  // index always lines up with the right color and the right row. (A
  // previous version sorted a second time right before rendering the
  // legend, which mutated the array in place -- since Recharts reads the
  // `data` prop after this function returns, that caused each Cell's color
  // to line up with the WRONG slice by index once the array got reordered.)
  const chartData = Object.entries(data.sources)
    .map(([key, value]) => ({
      key,
      name: SOURCE_LABELS[key],
      value,
      color: SOURCE_COLORS[key],
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 17, margin: 0 }}>
          Source Attribution — {data.point}
        </h3>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5cm", flexWrap: "wrap" }}>
        <div style={{ flex: "0 0 auto", width: "min(100%, 340px)" }}>
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius="60%"
                outerRadius="98%"
                paddingAngle={2}
                isAnimationActive={false}
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
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: "1 1 200px", minWidth: 200 }}>
          {chartData.map((entry) => (
            <div key={entry.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 12, height: 12, borderRadius: 3, background: entry.color, display: "inline-block", flexShrink: 0 }} />
                <span style={{ color: "var(--text-secondary)" }}>{entry.name}</span>
              </div>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginRight: "2cm" }}>{entry.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
