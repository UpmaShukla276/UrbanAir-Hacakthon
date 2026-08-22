import React, { useState, useRef, useCallback } from "react";
import { api } from "../api";

export default function SearchBar({ onSelectLocation }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef(null);

  const runSearch = useCallback(async (q) => {
    if (q.trim().length < 3) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const res = await api.searchLocation(q);
      setResults(res);
      setOpen(true);
    } catch (e) {
      console.error("Search failed", e);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(val), 450);
  };

  const handleSelect = (result) => {
    setQuery(result.name.split(",")[0]);
    setOpen(false);
    setResults([]);
    onSelectLocation(result);
  };

  return (
    <div style={{ position: "relative", width: 180 }}>
      <input
        type="text"
        value={query}
        onChange={handleChange}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search any place in NCR..."
        style={{
          width: "100%",
          background: "var(--bg-panel-raised)",
          color: "var(--text-primary)",
          border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius-sm)",
          padding: "8px 12px",
          fontSize: 13,
          fontFamily: "var(--font-body)",
        }}
      />
      {loading && (
        <span style={{ position: "absolute", right: 10, top: 9, fontSize: 11, color: "var(--text-tertiary)" }}>...</span>
      )}
      {open && results.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: "var(--bg-panel-raised)",
            border: "1px solid var(--border-strong)",
            borderRadius: "var(--radius-sm)",
            zIndex: 2000,
            maxHeight: 220,
            overflowY: "auto",
          }}
        >
          {results.map((r, i) => (
            <div
              key={i}
              onClick={() => handleSelect(r)}
              style={{
                padding: "8px 12px",
                fontSize: 12,
                color: "var(--text-secondary)",
                cursor: "pointer",
                borderBottom: i < results.length - 1 ? "1px solid var(--border-subtle)" : "none",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-panel)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {r.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
