import React from "react";

function Section({ label, children, accentColor = "var(--accent)" }) {
  return (
    <div style={{ paddingLeft: 12, borderLeft: `2px solid ${accentColor}` }}>
      <div
        style={{
          fontFamily: "var(--font-mono)", fontSize: 10.5, letterSpacing: "0.06em",
          textTransform: "uppercase", color: accentColor, marginBottom: 8,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.65 }}>
        {children}
      </div>
    </div>
  );
}

const STAGES = [
  { label: "Stage I", category: "Poor", range: "201–300", color: "#FF7A00" },
  { label: "Stage II", category: "Very Poor", range: "301–400", color: "#D9534F" },
  { label: "Stage III", category: "Severe", range: "401–450", color: "#7B1F1F" },
  { label: "Stage IV", category: "Severe+", range: ">450", color: "#4A0E0E" },
];

export default function GrapInfoPanel() {
  return (
    <div
      style={{
        background: "var(--bg-panel)", border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)", padding: 24, flex: "1 1 420px", minWidth: 420,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--accent)", display: "inline-block" }} />
        <h4 style={{ fontFamily: "var(--font-display)", fontSize: 16, margin: 0 }}>
          About this panel
        </h4>
      </div>
      <p style={{ fontSize: 12.5, color: "var(--text-tertiary)", margin: "8px 0 22px 0", lineHeight: 1.6, maxWidth: 640 }}>
        A quick reference for what GRAP Compliance measures, why it's here, and how to read the zone list on the left.
      </p>

      <div
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "24px 32px",
        }}
      >
        <Section label="What this shows">
          For each of Delhi NCR's 21 monitored zones: exactly which{" "}
          <strong style={{ color: "var(--text-primary)" }}>GRAP stage</strong> applies
          right now — not one number for the whole NCR average (like CAQM's
          own dashboard shows), but zone-by-zone, since one part of the
          city can be in Stage III while another is clear.
        </Section>

        <Section label="Why it's here" accentColor="var(--aqi-satisfactory)">
          GRAP mandates specific, legally-binding restrictions once AQI
          crosses each threshold — construction bans, truck entry bans,
          school closures. An official needs to know exactly which
          zone triggered which stage, and which actions apply, without
          digging through the CAQM order manually.
        </Section>

        <Section label="How it's calculated" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            Each zone's <strong style={{ color: "var(--text-primary)" }}>current AQI</strong> and{" "}
            <strong style={{ color: "var(--text-primary)" }}>24h forecast</strong> are both
            checked against CAQM's stage bands. Whichever is higher decides
            the stage shown.
          </div>
          <div>
            This mirrors CAQM's real protocol: a stage is invoked{" "}
            <strong style={{ color: "var(--text-primary)" }}>proactively</strong> when a
            higher AQI is forecast to sustain — not only after it's
            already happened.
          </div>
        </Section>

        <Section label="Reading the badges" accentColor="var(--aqi-poor)">
          A grey "No GRAP stage" badge means AQI is below 201 — good news,
          no restrictions apply. An orange/red badge names the active
          stage. A ⚠ warning means the +24h forecast crosses into a
          higher stage than right now — act before it arrives.
        </Section>
      </div>

      <div style={{ marginTop: 22, paddingTop: 14, borderTop: "1px solid var(--border-subtle)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--text-tertiary)", marginBottom: 10 }}>
          The 4 stages
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {STAGES.map((s) => (
            <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: 10.5, fontWeight: 600, color: "#fff",
                background: s.color, borderRadius: 4, padding: "2px 7px", minWidth: 52, textAlign: "center",
              }}>
                {s.label}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                {s.category} <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-tertiary)" }}>· AQI {s.range}</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 18, paddingTop: 14 }}>
        Source: CAQM revised GRAP schedule (21.11.2025), caqm.nic.in.
      </div>
    </div>
  );
}