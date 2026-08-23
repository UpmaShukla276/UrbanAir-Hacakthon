import React, { useState } from "react";

const QUESTIONS = [
  {
    label: "What this shows",
    accentColor: "var(--accent)",
    content: (
      <>
        For each of Delhi NCR's 21 monitored areas: what % of current
        pollution is coming from <strong style={{ color: "var(--text-primary)" }}>Traffic</strong>,{" "}
        <strong style={{ color: "var(--text-primary)" }}>Industrial</strong>,{" "}
        <strong style={{ color: "var(--text-primary)" }}>Construction</strong>,{" "}
        <strong style={{ color: "var(--text-primary)" }}>Waste/Stubble-Burning</strong>, and
        non-local <strong style={{ color: "var(--text-primary)" }}>Regional Background</strong>.
        "Compare all locations" stacks all 21 side-by-side so you can
        spot which area's dominant source stands out.
      </>
    ),
  },
  {
    label: "Why it's here",
    accentColor: "var(--aqi-satisfactory)",
    content: (
      <>
        Knowing the AQI number doesn't tell you what to *do* about it —
        two areas at the same AQI can need completely different
        responses (traffic curbs vs. industrial inspection vs.
        cross-state stubble-burning coordination). This is the
        reasoning layer that Enforcement and What-if Simulation both
        build on top of.
      </>
    ),
  },
  {
    label: "How it's calculated",
    accentColor: "var(--accent-dim)",
    content: (
      <>
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
      </>
    ),
  },
  {
    label: "Reading the breakdown",
    accentColor: "var(--aqi-poor)",
    content: (
      <>
        <div>
          The breakdown is based on the current pollution mix for the selected area,
          combining local activity signals with dispersion conditions and seasonal context.
        </div>
      </>
    ),
  },
];

function AccordionItem({ label, accentColor, content, isOpen, onToggle }) {
  return (
    <div style={{ borderBottom: "1px solid var(--border-subtle)" }}>
      <button
        onClick={onToggle}
        style={{
          width: "100%",
          background: "none",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 2px",
          textAlign: "left",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: isOpen ? accentColor : "var(--text-primary)",
            fontWeight: 600,
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: 14,
            color: accentColor,
            transform: isOpen ? "rotate(45deg)" : "rotate(0deg)",
            transition: "transform 0.15s ease",
            flexShrink: 0,
            marginLeft: 12,
          }}
        >
          +
        </span>
      </button>
      {isOpen && (
        <div
          style={{
            paddingLeft: 12,
            borderLeft: `2px solid ${accentColor}`,
            margin: "0 2px 16px 2px",
            fontSize: 13.5,
            color: "var(--text-secondary)",
            lineHeight: 1.65,
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
}

export default function SourceAttributionInfoPanel() {
  const [openIndex, setOpenIndex] = useState(0); // first question open by default

  return (
    <div
      style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: 24,
        height: "100%",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--accent)", display: "inline-block" }} />
        <h4 style={{ fontFamily: "var(--font-display)", fontSize: 16, margin: 0 }}>
          About this panel
        </h4>
      </div>
      <p style={{ fontSize: 12.5, color: "var(--text-tertiary)", margin: "8px 0 18px 0", lineHeight: 1.6 }}>
        Tap a question to expand it.
      </p>

      <div>
        {QUESTIONS.map((q, i) => (
          <AccordionItem
            key={q.label}
            label={q.label}
            accentColor={q.accentColor}
            content={q.content}
            isOpen={openIndex === i}
            onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
          />
        ))}
      </div>
    </div>
  );
}
