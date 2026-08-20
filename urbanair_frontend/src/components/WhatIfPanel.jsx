import React, { useState } from "react";
import { severityFor } from "./AqiGauge";
import { api } from "../api";

const SLIDERS = [
  { key: "reduce_traffic_pct", label: "Reduce Traffic", color: "#FF7A00" },
  { key: "reduce_industrial_pct", label: "Reduce Industrial", color: "#D9534F" },
  { key: "reduce_construction_pct", label: "Reduce Construction", color: "#8B96A5" },
  { key: "reduce_waste_burning_pct", label: "Reduce Waste Burning", color: "#FFC107" },
];

export default function WhatIfPanel({ points, selectedPoint, onSelectPoint }) {
  const [reductions, setReductions] = useState({
    reduce_traffic_pct: 0,
    reduce_industrial_pct: 0,
    reduce_construction_pct: 0,
    reduce_waste_burning_pct: 0,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await api.whatif({ point: selectedPoint, ...reductions });
      setResult(res);
    } catch (e) {
      console.error("Whatif failed", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          What-if Simulation
        </h3>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-tertiary)" }}>
          scenario planning
        </span>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "var(--text-tertiary)", display: "block", marginBottom: 6 }}>Location</label>
        <select
          value={selectedPoint}
          onChange={(e) => onSelectPoint(e.target.value)}
          style={{
            background: "var(--bg-panel-raised)", color: "var(--text-primary)",
            border: "1px solid var(--border-strong)", borderRadius: "var(--radius-sm)",
            padding: "8px 12px", fontSize: 13, width: "100%",
          }}
        >
          {points.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 16 }}>
        {SLIDERS.map((s) => (
          <div key={s.key}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: "var(--text-secondary)" }}>{s.label}</span>
              <span style={{ fontFamily: "var(--font-mono)", color: s.color }}>{reductions[s.key]}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={reductions[s.key]}
              onChange={(e) => setReductions((prev) => ({ ...prev, [s.key]: Number(e.target.value) }))}
              style={{ width: "100%", accentColor: s.color }}
            />
          </div>
        ))}
      </div>

      <button
        onClick={runSimulation}
        disabled={loading}
        style={{
          width: "100%", background: "var(--accent)", color: "var(--bg-base)",
          border: "none", borderRadius: "var(--radius-sm)", padding: "10px 0",
          fontSize: 13, fontWeight: 600, cursor: "pointer", marginBottom: 16,
        }}
      >
        {loading ? "Simulating..." : "Run Simulation"}
      </button>

      {result && (
        <div style={{ background: "var(--bg-panel-raised)", borderRadius: "var(--radius-md)", padding: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", marginBottom: 12 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>BEFORE</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 28, fontWeight: 600, color: severityFor(result.current_aqi).color }}>
                {Math.round(result.current_aqi)}
              </div>
            </div>
            <div style={{ color: "var(--text-tertiary)", fontSize: 20 }}>→</div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>AFTER</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 28, fontWeight: 600, color: severityFor(result.simulated_aqi).color }}>
                {Math.round(result.simulated_aqi)}
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>IMPROVEMENT</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 600, color: "var(--accent)" }}>
                {result.improvement_pct}%
              </div>
            </div>
          </div>
          <div style={{ fontSize: 10, color: "var(--text-tertiary)", lineHeight: 1.5 }}>
            {result.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
