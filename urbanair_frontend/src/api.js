const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  cities: () => request("/cities"),
  current: (city) => request(`/current/${encodeURIComponent(city)}`),
  forecast: (city, referenceTime) =>
    request(
      `/forecast/${encodeURIComponent(city)}${referenceTime ? `?reference_time=${encodeURIComponent(referenceTime)}` : ""}`
    ),
  historical: (city, hours = 168) => request(`/historical/${encodeURIComponent(city)}?hours=${hours}`),
  geojson: (layer) => request(`/geojson/${layer}`),
  nowcast: (payload) =>
    request("/nowcast", { method: "POST", body: JSON.stringify(payload) }),
  sourceAttribution: (point) => request(`/source-attribution/${encodeURIComponent(point)}`),
  sourceAttributionAll: () => request("/source-attribution"),
  enforcement: () => request("/enforcement"),
  
  grapAll: () => request("/grap"),
  grapPoint: (point) => request(`/grap/${encodeURIComponent(point)}`),

  healthAdvisory: (city) => request(`/health-advisory/${encodeURIComponent(city)}`),
  healthAdvisoryAll: () => request("/health-advisory"),
  searchLocation: (query) => request(`/search-location?query=${encodeURIComponent(query)}`),
  estimate: (lat, lon) => request(`/estimate?lat=${lat}&lon=${lon}`),
  whatif: (payload) => request("/whatif", { method: "POST", body: JSON.stringify(payload) }),
  greenCoverAll: () => request("/green-cover"),
  greenCoverPoint: (point) => request(`/green-cover/${encodeURIComponent(point)}`),
};