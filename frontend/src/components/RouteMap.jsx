import { useEffect, useRef, useState, useMemo } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
maplibregl.setWorkerUrl(workerUrl);
import {
  collection,
  feature,
  routeColors,
  riskColors,
  conditionsAt,
  splitRoute,
  segmentRisk,
} from "../utils/geo";
export default function RouteMap({
  routes,
  selected,
  recommended,
  mode,
  hour,
  onSelect,
  onCheckpoint,
}) {
  const container = useRef(null),
    map = useRef(null),
    callbacks = useRef({}),
    [ready, setReady] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    callbacks.current = { onSelect, onCheckpoint };
  }, [onSelect, onCheckpoint]);
  const route = routes.find((r) => r.route_id === selected);
  const segments = useMemo(() => (route ? splitRoute(route) : []), [route]);
  useEffect(() => {
    let instance;
    let popup;
    let resizeObserver;
    try {
      instance = new maplibregl.Map({
        container: container.current,
        style: "https://tiles.openfreemap.org/styles/positron",
        center: [-85.8, 42],
        zoom: 5.8,
        attributionControl: true,
      });
      map.current = instance;
      resizeObserver = new ResizeObserver(() => instance.resize());
      resizeObserver.observe(container.current);
      instance.addControl(new maplibregl.NavigationControl(), "top-right");
      instance.on("error", (event) => {
        console.warn("Map error:", event.error?.message);
        setError(
          "Map could not load. Check your connection; route details remain available.",
        );
      });
      instance.on("load", () => {
        setError("");
        for (const id of ["routes", "segments", "points", "endpoints"])
          instance.addSource(id, { type: "geojson", data: collection([]) });
        instance.addLayer({
          id: "route-halo",
          type: "line",
          source: "routes",
          paint: { "line-color": "#ffffff", "line-width": 11 },
        });
        instance.addLayer({
          id: "routes",
          type: "line",
          source: "routes",
          paint: {
            "line-color": ["get", "color"],
            "line-width": ["case", ["get", "selected"], 7, 4],
            "line-opacity": 0.85,
          },
        });
        instance.addLayer({
          id: "corridor",
          type: "line",
          source: "segments",
          paint: {
            "line-color": ["get", "color"],
            "line-width": 20,
            "line-opacity": 0.2,
          },
        });
        instance.addLayer({
          id: "segments",
          type: "line",
          source: "segments",
          paint: { "line-color": ["get", "color"], "line-width": 7 },
        });
        instance.addLayer({
          id: "points",
          type: "circle",
          source: "points",
          paint: {
            "circle-color": ["get", "color"],
            "circle-radius": 5,
            "circle-stroke-color": "#fff",
            "circle-stroke-width": 2,
          },
        });
        instance.addLayer({
          id: "endpoints",
          type: "circle",
          source: "endpoints",
          paint: {
            "circle-color": ["get", "color"],
            "circle-radius": 9,
            "circle-stroke-color": "#fff",
            "circle-stroke-width": 3,
          },
        });
        instance.on("click", "routes", (e) =>
          callbacks.current.onSelect(e.features[0].properties.id),
        );
        instance.on("click", "points", (e) =>
          callbacks.current.onCheckpoint(e.features[0].properties.index),
        );
        popup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
        });
        instance.on("mousemove", "routes", (e) => {
          const p = e.features[0].properties;
          popup
            .setLngLat(e.lngLat)
            .setText(`Route ${p.id} | ${p.distance} mi | ${p.status}`)
            .addTo(instance);
        });
        instance.on("mouseleave", "routes", () => popup.remove());
        for (const layer of ["routes", "points"]) {
          instance.on("mouseenter", layer, () => {
            instance.getCanvas().style.cursor = "pointer";
          });
          instance.on("mouseleave", layer, () => {
            instance.getCanvas().style.cursor = "";
          });
        }
        setReady(true);
      });
    } catch (e) {
      queueMicrotask(() => setError(`Map unavailable: ${e.message}`));
    }
    return () => {
      resizeObserver?.disconnect();
      popup?.remove();
      instance?.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    if (!ready) return;
    const m = map.current;
    m.getSource("routes").setData(
      collection(
        routes.map((r) =>
          feature("LineString", r.geometry, {
            id: r.route_id,
            distance: r.distance_miles.toFixed(1),
            status: r.contains_no_travel
              ? "No Travel - excluded"
              : r.route_id === recommended
                ? "Recommended"
                : "Alternative",
            selected: r.route_id === selected,
            color: r.contains_no_travel
              ? riskColors["No Travel"]
              : r.route_id === recommended
                ? "#5065da"
                : routeColors[
                    1 +
                      (routes
                        .filter(
                          (candidate) => candidate.route_id !== recommended,
                        )
                        .findIndex(
                          (candidate) => candidate.route_id === r.route_id,
                        ) %
                        2)
                  ],
          }),
        ),
      ),
    );
    m.getSource("segments").setData(
      collection(
        mode === "routes"
          ? []
          : segments.map((coords, i) =>
              feature("LineString", coords, {
                color:
                  riskColors[
                    segmentRisk(
                      conditionsAt(route.checkpoints[i], mode, hour),
                      conditionsAt(route.checkpoints[i + 1], mode, hour),
                    )
                  ],
              }),
            ),
      ),
    );
    m.getSource("points").setData(
      collection(
        (route?.checkpoints || []).map((cp, i) =>
          feature("Point", [cp.lon, cp.lat], {
            index: i,
            color:
              riskColors[conditionsAt(cp, mode, hour)?.risk?.overall_risk] ||
              riskColors.Unavailable,
          }),
        ),
      ),
    );
    m.getSource("endpoints").setData(
      collection(
        route
          ? [
              feature("Point", route.geometry[0], { color: "#152b42" }),
              feature("Point", route.geometry.at(-1), { color: "#5065da" }),
            ]
          : [],
      ),
    );
  }, [ready, routes, selected, recommended, mode, hour, route, segments]);
  useEffect(() => {
    if (!ready || !routes.length) return;
    const bounds = new maplibregl.LngLatBounds();
    routes.forEach((r) => r.geometry.forEach((p) => bounds.extend(p)));
    map.current.fitBounds(bounds, { padding: 70, maxZoom: 11, duration: 800 });
  }, [ready, routes]);
  return (
    <>
      <div
        ref={container}
        className="map"
        aria-label="Interactive truck route map"
      />
      {error && (
        <div className="map-error" role="status">
          {error}
        </div>
      )}
    </>
  );
}
