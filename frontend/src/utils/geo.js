export const riskColors = {
  Low: "#20956b",
  Moderate: "#d7ac16",
  High: "#ed852c",
  Severe: "#df424c",
  "No Travel": "#851d36",
  Unavailable: "#8795a9",
};
export const riskLevels = Object.keys(riskColors).slice(0, 5);
export const routeColors = ["#5065da", "#0b9698", "#a16bc2"];
export const collection = (features) => ({
  type: "FeatureCollection",
  features,
});
export const feature = (type, coordinates, properties) => ({
  type: "Feature",
  geometry: { type, coordinates },
  properties,
});
export const conditionsAt = (cp, mode, hour) =>
  mode === "forecast" ? cp.hourly_forecast?.[hour] : cp;
export function distance(a, b) {
  const rad = (x) => (x * Math.PI) / 180;
  const dlat = rad(b[1] - a[1]),
    dlon = rad(b[0] - a[0]);
  return (
    7917.52 *
    Math.asin(
      Math.min(
        1,
        Math.sqrt(
          Math.sin(dlat / 2) ** 2 +
            Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dlon / 2) ** 2,
        ),
      ),
    )
  );
}
// Same cumulative Haversine scaling and linear interpolation as routing.geometry.
export function splitRoute(route) {
  const coords = route.geometry,
    cumulative = [0];
  for (let i = 1; i < coords.length; i++)
    cumulative.push(cumulative[i - 1] + distance(coords[i - 1], coords[i]));
  const total = cumulative.at(-1);
  if (!total || !(route.distance_miles > 0)) return [];
  const at = (mile) => {
    const target = (mile / route.distance_miles) * total;
    let i = 1;
    while (i < coords.length - 1 && cumulative[i] < target) i++;
    const f =
      (target - cumulative[i - 1]) / (cumulative[i] - cumulative[i - 1] || 1);
    return coords[i - 1].map(
      (v, j) => v + (coords[i][j] - v) * Math.max(0, Math.min(1, f)),
    );
  };
  return route.checkpoints.slice(1).map((cp, i) => {
    const start = route.checkpoints[i].mile,
      end = cp.mile;
    return [
      at(start),
      ...coords.filter(
        (_, j) =>
          (cumulative[j] / total) * route.distance_miles > start &&
          (cumulative[j] / total) * route.distance_miles < end,
      ),
      at(end),
    ];
  });
}
export function segmentRisk(a, b) {
  if (!a?.risk || !b?.risk) return "Unavailable";
  return (
    riskLevels[
      Math.max(
        riskLevels.indexOf(a.risk.overall_risk),
        riskLevels.indexOf(b.risk.overall_risk),
      )
    ] || "Unavailable"
  );
}
export const stamp = (s) =>
  s
    ? new Date(s).toLocaleString(undefined, {
        timeZone: "UTC",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }) + " UTC"
    : "Unavailable";
export const number = (n) =>
  Number.isFinite(n)
    ? n.toLocaleString(undefined, { maximumFractionDigits: 1 })
    : "--";
