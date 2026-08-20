import React from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

function formatTick(ts) {
  const d = new Date(ts);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const d = new Date(label);
  return (
    <div
      style={{
        background: "var(--bg-panel-raised)",
        border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius-sm)",
        padding: "8px 12px",
        fontFamily: "var(--font-mono)",
        fontSize: 12,
      }}
    >
      <div style={{ color: "var(--text-tertiary)", marginBottom: 4 }}>
        {d.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
      </div>
      <div style={{ color: "var(--accent)" }}>AQI {Math.round(payload[0].value)}</div>
    </div>
  );
}

export default function TrendChart({ data }) {
  if (!data || data.length === 0) return null;

  const hoursSpan = data.length; // hourly-resolution live series
  const title = hoursSpan >= 168 ? "7-day trend" : `Trend (${hoursSpan}h of live data collected so far)`;

  return (
    <div>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: "0 0 12px 0" }}>
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTick}
            stroke="var(--text-tertiary)"
            fontSize={11}
            fontFamily="var(--font-mono)"
            tickLine={false}
            axisLine={{ stroke: "var(--border-subtle)" }}
            interval={Math.floor(data.length / 6)}
          />
          <YAxis
            stroke="var(--text-tertiary)"
            fontSize={11}
            fontFamily="var(--font-mono)"
            tickLine={false}
            axisLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={100} stroke="var(--aqi-moderate)" strokeDasharray="4 4" strokeOpacity={0.5} />
          <ReferenceLine y={200} stroke="var(--aqi-poor)" strokeDasharray="4 4" strokeOpacity={0.5} />
          <Area
            type="monotone"
            dataKey="aqi"
            stroke="var(--accent)"
            strokeWidth={2}
            fill="url(#aqiGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
