import { number } from "../utils/geo";
export default function RouteCard({ route, recommended, selected, onSelect }) {
  const miles = route.risk_miles || {};
  return (
    <button
      className={`route-card ${selected ? "selected" : ""}`}
      onClick={onSelect}
      aria-pressed={selected}
    >
      <div className="card-top">
        <strong>Route {route.route_id}</strong>
        <span className={`badge ${route.contains_no_travel ? "danger" : ""}`}>
          {route.contains_no_travel
            ? "No Travel - excluded"
            : recommended
              ? "Recommended"
              : "Alternative"}
        </span>
      </div>
      <div className="route-metrics">
        <strong>
          {number(route.distance_miles)} <small>mi</small>
        </strong>
        <strong>
          {Math.floor(route.duration_seconds / 3600)}h{" "}
          {Math.round((route.duration_seconds % 3600) / 60)}m
        </strong>
      </div>
      <div className="risk-strip">
        {Object.entries(miles).map(([risk, value]) => (
          <span
            key={risk}
            style={{
              flex: value,
              background: {
                Low: "#20956b",
                Moderate: "#d7ac16",
                High: "#ed852c",
                Severe: "#df424c",
                "No Travel": "#851d36",
              }[risk],
            }}
          />
        ))}
      </div>
      <div className="risk-grid">
        {["Severe", "High", "Moderate", "No Travel"].map((r) => (
          <span key={r}>
            {r}
            <b>{number(miles[r])} mi</b>
          </span>
        ))}
        <span>
          Average risk<b>{number(route.average_risk)} / 4</b>
        </span>
      </div>
    </button>
  );
}
