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

export default function WhatIfInfoPanel() {
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
        A quick reference for what What-if Simulation does, why it's here, and how to read the result on the left.
      </p>

      <div
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "24px 32px",
        }}
      >
        <Section label="What this does">
          Lets you drag sliders to ask "what if Traffic/Industrial/
          Construction/Waste-Burning at this location dropped by X%?" and
          shows the estimated new AQI and % improvement, before you
          actually run an enforcement action.
        </Section>

        <Section label="Why it's here" accentColor="var(--aqi-satisfactory)">
          Source Attribution tells you which sources contribute how much;
          this answers the natural next question officials ask —
          <strong style={{ color: "var(--text-primary)" }}> "which lever, pulled how hard,
          moves the number most?"</strong> Useful for comparing scenarios
          (e.g. a 30% traffic cut vs. a 50% construction-dust cut) before
          committing resources to one.
        </Section>

        <Section label="How it's calculated" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            Current AQI is split into a <strong style={{ color: "var(--text-primary)" }}>background floor</strong> (regional
            transport, not locally controllable) and a <strong style={{ color: "var(--text-primary)" }}>local slice</strong> divided
            across the 4 sources per their Source Attribution %.
          </div>
          <div>
            Your requested % reduction is applied to each source's slice
            only, then everything is added back up to get the simulated
            AQI — a <strong style={{ color: "var(--text-primary)" }}>linear-scaling estimate</strong>, not a physics-based
            dispersion model.
          </div>
        </Section>

        <Section label="Reading the result" accentColor="var(--aqi-poor)">
          <div style={{ marginBottom: 10 }}>
            The background floor is the AQI you'd still see even at 100%
            reduction on every slider — it can never go to zero.
          </div>
          <div>
            Treat the improvement % as a "which lever matters more"
            comparison tool, not a guaranteed real-world outcome — actual
            air chemistry (e.g. NOx-O3 interaction) isn't purely linear.
          </div>
        </Section>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 22, paddingTop: 14 }}>
        This is a scenario-planning tool for comparing options, not a
        validated atmospheric model or a regulatory-grade forecast.
      </div>
    </div>
  );
}
