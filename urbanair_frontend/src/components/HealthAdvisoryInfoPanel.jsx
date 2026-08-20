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

export default function HealthAdvisoryInfoPanel() {
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
        Plain-language, citizen-facing guidance — different audience from
        Enforcement, which is written for officials deciding where to act.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "24px 32px" }}>
        <Section label="Who this is for">
          General public and sensitive groups (people with asthma, lung or
          heart disease, children, older adults) deciding whether it's safe
          to go outside right now, or over the next 24–72 hours.
        </Section>

        <Section label="Single vs compare" accentColor="var(--aqi-satisfactory)">
          <strong style={{ color: "var(--text-primary)" }}>Single location</strong> gives
          your selected city's advisory plus a 3-horizon forecast strip.{" "}
          <strong style={{ color: "var(--text-primary)" }}>Compare all areas</strong> covers
          all 21 monitored points at once, sorted worst-first, so you can see
          which parts of NCR need the strongest caution today.
        </Section>

        <Section label="How the 21 points work" accentColor="var(--accent-dim)">
          <div style={{ marginBottom: 10 }}>
            5 cities (Delhi, Faridabad, Ghaziabad, Gurgaon, Noida) have their
            own trained nowcast model and live sensor feed.
          </div>
          <div>
            The other 16 — Delhi's official DPCC pollution hotspots plus a
            few high-footfall landmarks — don't have a dedicated sensor, so
            their AQI is <strong style={{ color: "var(--text-primary)" }}>proxied from the nearest
            trained city</strong>, labeled on each card with the distance. Same
            honest-proxy approach used elsewhere in the app (e.g. "Estimate
            any point" on the Overview map).
          </div>
        </Section>

        <Section label="Reading the severity colors" accentColor="var(--aqi-poor)">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div style={{ width: 40, height: 8, borderRadius: 6, background: "var(--aqi-good)", flexShrink: 0 }} />
            <span>Good / Satisfactory — no real restriction</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div style={{ width: 40, height: 8, borderRadius: 6, background: "var(--aqi-moderate)", flexShrink: 0 }} />
            <span>Moderate — sensitive groups should ease off exertion</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 40, height: 8, borderRadius: 6, background: "var(--aqi-severe)", flexShrink: 0 }} />
            <span>Very Poor / Severe — general public should limit outdoor exposure too</span>
          </div>
        </Section>
      </div>

      <div style={{ fontSize: 11, color: "var(--text-tertiary)", lineHeight: 1.6, borderTop: "1px solid var(--border-subtle)", marginTop: 22, paddingTop: 14 }}>
        Advisory text follows CPCB's standard AQI category bands — this app
        doesn't invent its own health thresholds.
      </div>
    </div>
  );
}
