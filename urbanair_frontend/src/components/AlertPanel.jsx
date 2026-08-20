import React, { useState } from "react";

export default function AlertPanel({ point }) {
  const [alertType, setAlertType] = useState("official");
  const [preview, setPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [toEmail, setToEmail] = useState("");
  const [sendStatus, setSendStatus] = useState(null);
  const [sending, setSending] = useState(false);

  const loadPreview = async (type) => {
    setAlertType(type);
    setPreview(null);
    setSendStatus(null);
    setLoadingPreview(true);
    try {
      const path = type === "official" ? "officials" : "public";
      const data = await fetch(`/api/alerts/${path}/${encodeURIComponent(point)}`).then((r) => r.json());
      setPreview(type === "official" ? data.report_text : data.message);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleSend = async () => {
    if (!toEmail) return;
    setSending(true);
    setSendStatus(null);
    try {
      const res = await fetch("/api/alerts/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ point, alert_type: alertType, to_email: toEmail }),
      });
      const data = await res.json();
      if (res.ok) {
        setSendStatus({ ok: true, msg: `Sent to ${data.to}` });
      } else {
        setSendStatus({ ok: false, msg: data.detail || "Failed to send" });
      }
    } catch (e) {
      setSendStatus({ ok: false, msg: String(e) });
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ marginTop: 14, borderTop: "1px solid var(--border-subtle)", paddingTop: 12 }}>
      <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
        <button
          onClick={() => loadPreview("official")}
          style={{
            background: alertType === "official" && preview ? "var(--accent)" : "var(--bg-panel)",
            color: alertType === "official" && preview ? "var(--bg-base)" : "var(--text-secondary)",
            border: "1px solid var(--border-strong)", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer",
          }}
        >
          Preview Official Report
        </button>
        <button
          onClick={() => loadPreview("public")}
          style={{
            background: alertType === "public" && preview ? "var(--accent)" : "var(--bg-panel)",
            color: alertType === "public" && preview ? "var(--bg-base)" : "var(--text-secondary)",
            border: "1px solid var(--border-strong)", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer",
          }}
        >
          Preview Public Advisory
        </button>
      </div>

      {loadingPreview && <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>Loading...</span>}

      {preview && (
        <>
          <pre
            style={{
              background: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 6,
              padding: 10,
              fontSize: 10.5,
              fontFamily: "var(--font-mono)",
              color: "var(--text-secondary)",
              whiteSpace: "pre-wrap",
              maxHeight: 220,
              overflowY: "auto",
              margin: "8px 0",
            }}
          >
            {preview}
          </pre>
          <div style={{ display: "flex", gap: 6 }}>
            <input
              type="email"
              placeholder="recipient@email.com"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              style={{
                flex: 1, background: "var(--bg-panel-raised)", color: "var(--text-primary)",
                border: "1px solid var(--border-strong)", borderRadius: 6, padding: "6px 10px", fontSize: 12,
              }}
            />
            <button
              onClick={handleSend}
              disabled={sending || !toEmail}
              style={{
                background: "var(--accent)", color: "var(--bg-base)", border: "none",
                borderRadius: 6, padding: "6px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer",
              }}
            >
              {sending ? "Sending..." : "Send"}
            </button>
          </div>
          {sendStatus && (
            <div style={{ fontSize: 11, marginTop: 6, color: sendStatus.ok ? "var(--aqi-good)" : "var(--aqi-poor)" }}>
              {sendStatus.msg}
            </div>
          )}
        </>
      )}
    </div>
  );
}
