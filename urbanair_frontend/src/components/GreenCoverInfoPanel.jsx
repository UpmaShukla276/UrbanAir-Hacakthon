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

export default function GreenCoverInfoPanel() {
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
        A quick reference for what Green Cover Index measures, why it's here, and how to read the numbers on the left.
      </p>

      <div
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "24px 32px",
        }}
      >
        <Section label="What this shows">
          For each of Delhi NCR's 21 monitored areas: how much tree-covered
          green space exists per resident, compared against a planning
          benchmark of <strong style={{ color: "var(--text-primary)" }}>9 sq.m per person</strong>.
          Areas falling short are flagged with an estimated tree count to
          close the gap.
        </Section>

        <Section label="Why it's here" accentColor="var(--aqi-satisfactory)">
          Pollution monitoring alone tells you the problem; green cover
          points at one lever to fix it — vegetation filters particulate
          matter and moderates local heat. This ties the dashboard directly
          to the <strong style={{ color: "var(--text-primary)" }}>Ek Ped Maa Ke Naam</strong> national
          afforestation drive, giving officials an area-wise planting
          priority list instead of a generic city-wide target.
        </Section>

        <Section label="How it's calculated" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            <strong style={{ color: "var(--text-primary)" }}>Tree cover %</strong> — ESA WorldCover
            10m-resolution satellite data (2021), sampled in a 2km radius
            around each area's centroid.
          </div>
          <div style={{ marginBottom: 10 }}>
            <strong style={{ color: "var(--text-primary)" }}>Population</strong> — Census 2011
            district-level density, mapped to each area (see <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>green_cover.py</code>).
          </div>
          <div>
            <strong style={{ color: "var(--text-primary)" }}>Trees needed</strong> — illustrative
            only: area deficit ÷ average mature-tree canopy size, not a
            literal planting order.
          </div>
        </Section>

        <Section label="Reading the bars" accentColor="var(--aqi-poor)">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <div style={{ width: 40, height: 8, borderRadius: 6, background: "var(--aqi-poor)", flexShrink: 0 }} />
            <span>Below the 9 sq.m/person benchmark</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <div style={{ width: 40, height: 8, borderRadius: 6, background: "var(--aqi-good)", flexShrink: 0 }} />
            <span>Meets or exceeds the benchmark</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 2, height: 14, background: "var(--text-tertiary)", flexShrink: 0 }} />
            <span>The tick mark on each bar is the benchmark line itself</span>
          </div>
        </Section>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 22, paddingTop: 14 }}>
        Treat every figure here as a planning-grade estimate, not a
        survey-grade measurement — see the caveats at the bottom of the
        main panel for specifics.
      </div>
    </div>
  );
}
