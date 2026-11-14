import { useState, useRef, useEffect } from "react";
import { planTrip, validateTrip } from "../api/routingApi";
export function useTripPlanner() {
  const [result, setResult] = useState(null),
    [selected, setSelected] = useState(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState("");
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);
  async function submit(trip) {
    if (loading) return;
    setError("");
    let payload;
    try {
      payload = validateTrip(trip);
    } catch (e) {
      setError(e.message);
      return;
    }
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    try {
      const data = await planTrip(payload, controller.signal);
      if (request.current === controller && !controller.signal.aborted) {
        setResult(data);
        setSelected(data.recommended_route_id ?? data.routes[0].route_id);
      }
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      if (request.current === controller) setLoading(false);
    }
  }
  return { result, selected, setSelected, loading, error, submit };
}
