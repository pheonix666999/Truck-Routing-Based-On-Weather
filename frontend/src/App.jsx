import { useState } from "react";
import {
  Route,
  ShieldCheck,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useTripPlanner } from "./hooks/useTripPlanner";
import TripForm from "./components/TripForm";
import RouteCard from "./components/RouteCard";
import RouteMap from "./components/RouteMap";
import ForecastTimeline from "./components/ForecastTimeline";
import CheckpointDetails from "./components/CheckpointDetails";
import ServerStatus from "./components/ServerStatus";
import { riskColors, number } from "./utils/geo";
import "./App.css";
const emptyRoutes = [];
export default function App() {
  const { result, selected, setSelected, loading, error, submit } =
    useTripPlanner();
  const [mode, setMode] = useState("routes"),
    [hour, setHour] = useState(0),
    [checkpoint, setCheckpoint] = useState(null),
    [collapsed, setCollapsed] = useState(false);
  const routes = result?.routes || emptyRoutes,
    route = routes.find((r) => r.route_id === selected);
  function select(id) {
    setSelected(id);
    setCheckpoint(null);
  }
  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-icon">
            <Route size={24} />
          </span>
          Weather<span>Route</span>
        </a>
        <ServerStatus />
      </header>
      <div className={`workspace-layout ${collapsed ? "collapsed" : ""}`}>
        <aside className="sidebar">
          <div className="sidebar-title">
            <button
              className="collapse"
              aria-label="Collapse planning panel"
              onClick={() => setCollapsed(true)}
            >
              <PanelLeftClose size={20} />
            </button>
          </div>
          <div className="sidebar-scroll">
            <TripForm onSubmit={submit} loading={loading} />
            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
            {loading && (
              <div className="loading" role="status">
                <div className="shimmer" />
                <p>Finding truck routes and checking hourly weather...</p>
                <small>This may take a minute on longer routes.</small>
              </div>
            )}
            <section className="comparison">
              <div className="section-heading">
                <h2>Route comparison</h2>
                <span>{routes.length} routes</span>
              </div>
              {!result ? (
                <div className="empty">
                  <ShieldCheck size={30} />
                  <h3>No routes yet</h3>
                </div>
              ) : (
                <>
                  {result.recommended_route_id == null ? (
                    <div className="error" role="alert">
                      No route can be recommended. All returned routes contain
                      No Travel conditions.
                    </div>
                  ) : (
                    <div className="recommendation">
                      <ShieldCheck size={20} />
                      <p>
                        <strong>
                          Route {result.recommended_route_id} ranks first
                        </strong>
                        <br />
                        Fewest Severe miles, then High miles, average risk and
                        travel time. No Travel routes are excluded.
                      </p>
                    </div>
                  )}
                  {routes.map((r) => (
                    <RouteCard
                      key={r.route_id}
                      route={r}
                      recommended={r.route_id === result.recommended_route_id}
                      selected={selected === r.route_id}
                      onSelect={() => select(r.route_id)}
                    />
                  ))}
                </>
              )}
            </section>
            {route && (
              <section className="checkpoint-list">
                <div className="section-label">
                  WEATHER CHECKPOINTS / ROUTE {selected}
                </div>
                <p className="hint">Select a point here or on the map.</p>
                <div>
                  {route.checkpoints.map((cp, i) => (
                    <button
                      key={i}
                      aria-pressed={checkpoint === i}
                      onClick={() => setCheckpoint(i)}
                    >
                      Mile {number(cp.mile)}
                    </button>
                  ))}
                </div>
              </section>
            )}
          </div>
        </aside>
        <main className="map-area">
          <RouteMap
            routes={routes}
            selected={selected}
            recommended={result?.recommended_route_id}
            mode={mode}
            hour={hour}
            onSelect={select}
            onCheckpoint={setCheckpoint}
          />
          <div className="map-toolbar">
            {collapsed && (
              <button
                aria-label="Open planning panel"
                onClick={() => setCollapsed(false)}
              >
                <PanelLeftOpen size={19} />
              </button>
            )}
            <div className="mode-switch" aria-label="Map mode">
              {[
                ["routes", "Route comparison"],
                ["risk", "Weather risk"],
                ["forecast", "48h forecast"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  aria-pressed={mode === key}
                  onClick={() => setMode(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          {route && (
            <div className="map-route-label">
              <strong>Route {selected}</strong>
              <span>
                {number(route.distance_miles)} mi / {route.checkpoints.length}{" "}
                weather checkpoints
              </span>
            </div>
          )}
          {route && checkpoint != null && route.checkpoints[checkpoint] && (
            <CheckpointDetails
              checkpoint={route.checkpoints[checkpoint]}
              mode={mode}
              hour={hour}
              onClose={() => setCheckpoint(null)}
            />
          )}
          <div className="map-bottom">
            <div className="legend">
              <strong>
                {mode === "routes"
                  ? "Checkpoint risk at ETA"
                  : "Estimated segment risk"}
              </strong>
              <div>
                {Object.entries(riskColors).map(([label, color]) => (
                  <span key={label}>
                    <i style={{ background: color }} />
                    {label}
                  </span>
                ))}
              </div>
              <p>
                {mode === "routes"
                  ? "Purple: recommended / teal / lilac: alternatives / dark red: excluded"
                  : "Each road interval uses the higher risk of its two endpoint checkpoints."}
              </p>
            </div>
            {mode === "forecast" &&
              (route ? (
                <ForecastTimeline
                  key={selected}
                  times={route.forecast_times}
                  hour={hour}
                  setHour={setHour}
                />
              ) : (
                <div className="timeline">
                  Plan a trip to load the real hourly corridor forecast.
                </div>
              ))}
          </div>
        </main>
      </div>
    </div>
  );
}
