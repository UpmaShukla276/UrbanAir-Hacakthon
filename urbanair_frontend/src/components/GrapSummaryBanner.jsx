import React from "react";

export default function GrapSummaryBanner({ data }) {
  if (!data || data.length === 0) return null;

  const counts = { 1: 0, 2: 0, 3: 0, 4: 0, clear: 0 };
  let mostSevere = null;
  let escalatingCount = 0;

  data.forEach((item) => {
    const stage = item.recommended_stage;
    if (stage) {
      counts[stage.stage] += 1;
      if (!mostSevere || stage.stage > mostSevere.recommended_stage.stage) mostSevere = item;
    } else {
      counts.clear += 1;
    }
    if (item.escalation_warning) escalatingCount += 1;
  });

  const activeStages = [1, 2, 3, 4].filter((s) => counts[s] > 0);

  return (
    <div style={{ marginBottom: 16, display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", height: 8, borderRadius: 4, overflow: "hidden" }}>
        {counts.clear > 0 && <div style={{ flex: counts.clear, background: "var(--border-subtle)" }} />}
        {counts[1] > 0 && <div style={{ flex: counts[1], background: "#FF7A00" }} />}
        {counts[2] > 0 && <div style={{ flex: counts[2], background: "#D9534F" }} />}
        {counts[3] > 0 && <div style={{ flex: counts[3], background: "#7B1F1F" }} />}
        {counts[4] > 0 && <div style={{ flex: counts[4], background: "#4A0E0E" }} />}
      </div>

      <div style={{
        display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center",
        background: "var(--bg-panel-raised)", border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)", padding: "14px 18px",
      }}>
        <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          <strong style={{ color: "var(--text-primary)" }}>{counts.clear}</strong> zones clear
        </span>
        {activeStages.length === 0 ? (
          <span style={{ fontSize: 13, color: "var(--aqi-satisfactory)" }}>· No GRAP stage active anywhere in NCR right now</span>
        ) : (
          activeStages.map((s) => (
            <span key={s} style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              · <strong style={{ color: "var(--text-primary)" }}>{counts[s]}</strong> in Stage {["", "I", "II", "III", "IV"][s]}
            </span>
          ))
        )}
      </div>

      {mostSevere && (
        <div style={{
          background: "rgba(217,83,79,0.08)", border: "1px solid var(--aqi-poor)",
          borderRadius: "var(--radius-md)", padding: "10px 16px", fontSize: 13,
        }}>
          Most critical zone right now: <strong>{mostSevere.point}</strong> — {mostSevere.recommended_stage.label} ({mostSevere.recommended_stage.category})
        </div>
      )}

      {escalatingCount > 0 && (
        <div style={{
          background: "rgba(255,122,0,0.08)", border: "1px solid #FF7A00",
          borderRadius: "var(--radius-md)", padding: "10px 16px", fontSize: 13, color: "#FF7A00",
        }}>
          ⚠ {escalatingCount} zone{escalatingCount > 1 ? "s" : ""} will cross into a higher stage within 24h — act before it arrives
        </div>
      )}
    </div>
  );
}