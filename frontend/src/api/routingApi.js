const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export async function searchLocations(query, signal) {
  const response = await fetch(
    `${base}/api/locations/?q=${encodeURIComponent(query)}`,
    { signal },
  );
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(data?.error || "Location search is unavailable.");
  return Array.isArray(data) ? data : [];
}

export async function checkLocationCoverage(latitude, longitude, signal) {
  const params = new URLSearchParams({ lat: latitude, lon: longitude });
  const response = await fetch(`${base}/api/coverage/?${params}`, { signal });
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(data?.error || "Routing coverage could not be verified.");
  return data?.covered === true;
}

export function validateTrip(trip) {
  if (!trip.origin.trim() || !trip.destination.trim())
    throw new Error("Enter an origin and destination.");
  if (!Number.isFinite(+trip.load_weight) || +trip.load_weight <= 0)
    throw new Error("Load weight must be greater than zero.");
  const departure = new Date(
    /(Z|[+-]\d{2}:\d{2})$/.test(trip.departure_time)
      ? trip.departure_time
      : trip.departure_time + "Z",
  );
  if (
    !Number.isFinite(+departure) ||
    departure < new Date() ||
    departure > new Date(Date.now() + 5 * 86400000)
  )
    throw new Error(
      "Choose a departure in the next five days. Arrival must also fall within forecast coverage.",
    );
  if (![10, 25, 50].includes(+trip.checkpoint_interval))
    throw new Error("Choose a valid checkpoint interval.");
  return {
    ...trip,
    departure_time: departure.toISOString(),
    load_weight: +trip.load_weight,
    checkpoint_interval: +trip.checkpoint_interval,
  };
}
export async function planTrip(trip, signal) {
  const response = await fetch(`${base}/api/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(trip),
    signal,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(
      data
        ? Object.entries(data)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`)
            .join("; ")
        : `Server returned ${response.status}. Please try again.`,
    );
  if (
    !data ||
    !Array.isArray(data.routes) ||
    !data.routes.length ||
    data.routes.some(
      (r) =>
        !Array.isArray(r.geometry) ||
        r.geometry.length < 2 ||
        !r.geometry.every(
          (p) =>
            Array.isArray(p) &&
            p.length === 2 &&
            p.every(Number.isFinite) &&
            Math.abs(p[0]) <= 180 &&
            Math.abs(p[1]) <= 90,
        ) ||
        !Array.isArray(r.checkpoints),
    )
  )
    throw new Error("The server returned missing or invalid route data.");
  const summaries = [...(data.ranking || []), ...(data.excluded_routes || [])];
  return {
    ...data,
    routes: data.routes.map((r) => ({
      ...r,
      ...summaries.find((s) => s.route_id === r.route_id),
    })),
  };
}
