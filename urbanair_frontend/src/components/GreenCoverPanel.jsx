import React, { useState, useEffect, useCallback } from "react";
import { api } from "../api";

function GreenBar({ value, benchmark, meetsBenchmark }) {
  const pct = Math.min(100, (value / (benchmark * 2)) * 100); // scale so 2x benchmark = full bar
  return (
    <div style={{ background: "var(--bg-base)", borderRadius: 6, height: 8, overflow: "hidden", position: "relative" }}>
      <div
        style={{
          width: `${pct}%`, height: "100%",
          background: meetsBenchmark ? "var(--aqi-good)" : "var(--aqi-poor)",
          transition: "width 0.4s ease",
        }}
      />
      <div
        style={{
          position: "absolute", left: "50%", top: 0, bottom: 0, width: 2,
          background: "var(--text-tertiary)",
        }}
        title={`Benchmark: ${benchmark} sq.m/person`}
      />
    </div>
  );
}

export default function GreenCoverPanel() {
  const [view, setView] = useState("compare"); // "single" | "compare"
  const [allData, setAllData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api.greenCoverAll().then(setAllData).catch((e) => console.error(e)).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <span style={{ color: "var(--text-tertiary)", fontSize: 13 }}>Computing tree cover from satellite data (~10s)...</span>;
  }
  if (!allData) return null;

  const sorted = [...allData].sort((a, b) => b.gap_sqm_per_capita - a.gap_sqm_per_capita);
  const totalTreesNeeded = allData.reduce((sum, d) => sum + d.illustrative_trees_needed, 0);
  const areasNotMeeting = allData.filter((d) => !d.meets_benchmark).length;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 15, margin: 0 }}>
          Green Cover Index
        </h3>
        <button
          onClick={load}
          className="refresh-btn"
        >
          ↻ Refresh
        </button>
      </div>
      <p style={{ fontSize: 11, color: "var(--text-tertiary)", margin: "0 0 16px 0", lineHeight: 1.5 }}>
        Tree cover from ESA WorldCover satellite data (10m resolution) vs. population,
        benchmarked against the widely-cited 9 sq.m green space/person planning target.
        Aligns with the <strong style={{ color: "var(--accent)" }}>Ek Ped Maa Ke Naam</strong> afforestation campaign.
      </p>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div style={{ flex: 1, background: "var(--bg-panel-raised)", borderRadius: "var(--radius-md)", padding: "12px 14px", textAlign: "center" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 600, color: "var(--aqi-poor)" }}>{areasNotMeeting}/{allData.length}</div>
          <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>areas below benchmark</div>
        </div>
        <div style={{ flex: 1, background: "var(--bg-panel-raised)", borderRadius: "var(--radius-md)", padding: "12px 14px", textAlign: "center" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 600, color: "var(--accent)" }}>{totalTreesNeeded.toLocaleString("en-IN")}</div>
          <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>illustrative trees needed (all areas)</div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {sorted.map((d) => (
          <div key={d.point} style={{ background: "var(--bg-panel-raised)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <strong style={{ fontSize: 13 }}>{d.point}</strong>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: d.meets_benchmark ? "var(--aqi-good)" : "var(--aqi-poor)" }}>
                {d.green_sqm_per_capita} / {d.benchmark_sqm_per_capita} sq.m per person
              </span>
            </div>
            <GreenBar value={d.green_sqm_per_capita} benchmark={d.benchmark_sqm_per_capita} meetsBenchmark={d.meets_benchmark} />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 11, color: "var(--text-tertiary)" }}>
              <span>Tree cover: {d.tree_cover_fraction_pct}% · Est. population: {d.estimated_population_in_radius.toLocaleString("en-IN")}</span>
              {!d.meets_benchmark && (
                <span style={{ color: "var(--accent)" }}>~{d.illustrative_trees_needed.toLocaleString("en-IN")} trees needed</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 9.5, color: "var(--text-tertiary)", marginTop: 14, lineHeight: 1.5, borderTop: "1px solid var(--border-subtle)", paddingTop: 10 }}>
        {allData[0]?.caveats?.map((c, i) => <div key={i}>• {c}</div>)}
      </div>
    </div>
  );
}
