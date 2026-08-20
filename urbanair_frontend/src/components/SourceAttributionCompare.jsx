import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

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
  background_pct: "Background",
};

export default function SourceAttributionCompare({ data, onRefresh, refreshing }) {
  if (!data || data.length === 0) return null;

  const chartData = data.map((d) => ({ point: d.point, ...d.sources }));
  const chartHeight = Math.max(320, chartData.length * 34 + 40);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          Compare all locations
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
            {chartData.length} areas
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

      <div style={{ maxHeight: 500, overflowY: chartHeight > 500 ? "auto" : "visible" }}>
        <ResponsiveContainer width="100%" height={chartHeight}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke="var(--text-tertiary)" fontSize={11} fontFamily="var(--font-mono)" unit="%" />
            <YAxis type="category" dataKey="point" stroke="var(--text-secondary)" fontSize={12} width={100} interval={0} />
            <Tooltip
              contentStyle={{ background: "var(--bg-panel-raised)", border: "1px solid var(--border-strong)", borderRadius: 8, fontFamily: "var(--font-mono)", fontSize: 12 }}
              formatter={(value, name) => [`${value}%`, SOURCE_LABELS[name]]}
            />
            <Legend
              formatter={(value) => SOURCE_LABELS[value]}
              wrapperStyle={{ fontSize: 12, fontFamily: "var(--font-body)", color: "var(--text-secondary)" }}
            />
            {Object.keys(SOURCE_COLORS).map((key) => (
              <Bar key={key} dataKey={key} stackId="a" fill={SOURCE_COLORS[key]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
