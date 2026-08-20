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

export default function SourceAttributionInfoPanel() {
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
        A quick reference for what Source Attribution measures, why it's here, and how to read the breakdown on the left.
      </p>

      <div
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "24px 32px",
        }}
      >
        <Section label="What this shows">
          For each of Delhi NCR's 21 monitored areas: what % of current
          pollution is coming from <strong style={{ color: "var(--text-primary)" }}>Traffic</strong>,{" "}
          <strong style={{ color: "var(--text-primary)" }}>Industrial</strong>,{" "}
          <strong style={{ color: "var(--text-primary)" }}>Construction</strong>,{" "}
          <strong style={{ color: "var(--text-primary)" }}>Waste/Stubble-Burning</strong>, and
          non-local <strong style={{ color: "var(--text-primary)" }}>Regional Background</strong>.
          "Compare all locations" stacks all 21 side-by-side so you can
          spot which area's dominant source stands out.
        </Section>

        <Section label="Why it's here" accentColor="var(--aqi-satisfactory)">
          Knowing the AQI number doesn't tell you what to *do* about it —
          two areas at the same AQI can need completely different
          responses (traffic curbs vs. industrial inspection vs.
          cross-state stubble-burning coordination). This is the
          reasoning layer that Enforcement and What-if Simulation both
          build on top of.
        </Section>

        <Section label="How it's calculated" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            <strong style={{ color: "var(--text-primary)" }}>Traffic</strong> — live congestion
            (TomTom). <strong style={{ color: "var(--text-primary)" }}>Industrial / Construction</strong> —
            proximity to known zones (OSM), weighted by live wind
            speed/direction carrying it toward the area.
          </div>
          <div>
            <strong style={{ color: "var(--text-primary)" }}>Waste-Burning</strong> — a seasonal
            heuristic: near-zero most of the year, rising sharply
            Oct–Nov if wind blows in from the NW (Punjab/Haryana
            stubble-burning season).
          </div>
        </Section>

        <Section label="Reading the breakdown" accentColor="var(--aqi-poor)">
          <div style={{ marginBottom: 10 }}>
            This is a <strong style={{ color: "var(--text-primary)" }}>transparent rule-based
            engine</strong>, not a trained ML classifier — there's no labeled
            "true pollution source" dataset to train against, and
            real-world agencies (CPCB/SAFAR) use similar rule +
            dispersion-model hybrids, not pure ML either.
          </div>
          <div>
            Every weight is a documented assumption based on known
            atmospheric behavior, not a fitted parameter — inspectable,
            not a black box.
          </div>
        </Section>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 22, paddingTop: 14 }}>
        Treat this as explainable reasoning for prioritizing action, not
        a certified source-apportionment measurement.
      </div>
    </div>
  );
}
