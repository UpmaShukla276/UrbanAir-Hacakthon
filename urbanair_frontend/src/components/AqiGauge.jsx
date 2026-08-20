import React from "react";

const SEVERITY_ORDER = [
  { max: 50, color: "var(--aqi-good)", label: "Good" },
  { max: 100, color: "var(--aqi-satisfactory)", label: "Satisfactory" },
  { max: 200, color: "var(--aqi-moderate)", label: "Moderate" },
  { max: 300, color: "var(--aqi-poor)", label: "Poor" },
  { max: 400, color: "var(--aqi-very-poor)", label: "Very Poor" },
  { max: Infinity, color: "var(--aqi-severe)", label: "Severe" },
];

function severityFor(aqi) {
  return SEVERITY_ORDER.find((s) => aqi <= s.max) ?? SEVERITY_ORDER[SEVERITY_ORDER.length - 1];
}

/**
 * Circular instrument-dial readout -- the visual signature of the dashboard.
 * Sweep fraction is capped at 500 AQI (CPCB's practical max band).
 */
export default function AqiGauge({ aqi, category, size = 220, subtitle }) {
  const sev = severityFor(aqi);
  const clamped = Math.min(aqi, 500);
  const fraction = clamped / 500;

  const strokeWidth = size * 0.07;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270-degree sweep, gauge-style
  const dashOffset = arcLength - fraction * arcLength;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(135deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border-subtle)"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={sev.color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease, stroke 0.3s ease" }}
        />
      </svg>
      <div
        style={{
          position: "relative",
          marginTop: -size * 0.62,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <span style={{ fontFamily: "var(--font-mono)", fontSize: size * 0.22, fontWeight: 600, color: sev.color, lineHeight: 1 }}>
          {Math.round(aqi)}
        </span>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", marginTop: 6, letterSpacing: 0.3 }}>
          {category || sev.label}
        </span>
        {subtitle && (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-tertiary)", marginTop: 2 }}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

export { severityFor, SEVERITY_ORDER };
