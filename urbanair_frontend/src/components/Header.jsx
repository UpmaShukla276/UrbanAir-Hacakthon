import React from "react";

export default function Header({ cities, selectedCity, onCityChange, lastUpdated }) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 28px",
        borderBottom: "1px solid var(--border-subtle)",
        background: "var(--bg-panel)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: "var(--accent)",
            boxShadow: "0 0 12px var(--accent)",
          }}
        />
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 20,
            fontWeight: 700,
            margin: 0,
            letterSpacing: 0.2,
          }}
        >
          UrbanAir <span style={{ color: "var(--accent)" }}>AI</span>
        </h1>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--text-tertiary)",
            border: "1px solid var(--border-strong)",
            borderRadius: 4,
            padding: "2px 8px",
            marginLeft: 4,
          }}
        >
          DELHI NCR
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        {lastUpdated && (
          <span style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-tertiary)" }}>
            <span
              className="live-pulse-dot"
              style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", display: "inline-block" }}
            />
            Updated {lastUpdated} · auto-refreshes every 60s
          </span>
        )}
        <select
          value={selectedCity}
          onChange={(e) => onCityChange(e.target.value)}
          style={{
            background: "var(--bg-panel-raised)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-strong)",
            borderRadius: "var(--radius-sm)",
            padding: "8px 14px",
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          {cities.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
