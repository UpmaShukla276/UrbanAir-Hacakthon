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

export default function EnforcementInfoPanel() {
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
        A quick reference for what Enforcement Priority Ranking does, why it's here, and how to read the list on the left.
      </p>

      <div
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "24px 32px",
        }}
      >
        <Section label="What this shows">
          All 21 monitored areas ranked by how urgently they need
          inspection/enforcement action right now, each with a
          plain-language <strong style={{ color: "var(--text-primary)" }}>Why</strong> (what's driving
          the score) and <strong style={{ color: "var(--text-primary)" }}>Action</strong> (what to do
          about it).
        </Section>

        <Section label="Why it's here" accentColor="var(--aqi-satisfactory)">
          With 21 areas and limited enforcement capacity, officials need
          to know where to send teams first, not just what the AQI is
          everywhere. This turns Source Attribution + forecast + traffic
          data into a single actionable priority order instead of 21
          separate numbers to compare manually.
        </Section>

        <Section label="How it's calculated" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            <strong style={{ color: "var(--text-primary)" }}>Priority score</strong> — a weighted
            blend: 50% forecasted AQI severity (24h ahead) + 25% traffic
            congestion + 25% strongest single source's intensity.
          </div>
          <div>
            <strong style={{ color: "var(--text-primary)" }}>Why / Action</strong> — rule-based
            triggers (e.g. industrial contribution over 15% adds
            "Significant industrial contribution" + an inspection action),
            not a black-box ranking.
          </div>
        </Section>

        <Section label="Reading the list" accentColor="var(--aqi-poor)">
          <div style={{ marginBottom: 10 }}>
            The number next to each area is its 24h-forecast AQI, not the
            current reading — this is a forward-looking priority list.
          </div>
          <div>
            "No acute signal — routine monitoring sufficient" for an area
            means none of the trigger thresholds were crossed, not that
            conditions are perfect.
          </div>
        </Section>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 22, paddingTop: 14 }}>
        Every weight and threshold here is a documented, transparent rule
        — not a trained model — so the reasoning behind each rank is
        always inspectable.
      </div>
    </div>
  );
}
