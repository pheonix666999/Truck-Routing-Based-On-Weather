// @vitest-environment jsdom
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import {
  checkLocationCoverage,
  validateTrip,
  planTrip,
  searchLocations,
} from "./api/routingApi";
import { riskColors, segmentRisk, splitRoute, conditionsAt } from "./utils/geo";
import RouteCard from "./components/RouteCard";
import ForecastTimeline from "./components/ForecastTimeline";
import TripForm from "./components/TripForm";
import App from "./App";
vi.mock("./components/RouteMap", () => ({ default: () => <div>Map</div> }));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const trip = {
  origin: "Chicago",
  destination: "Detroit",
  departure_time: new Date(Date.now() + 3600000).toISOString(),
  load_weight: 42000,
  checkpoint_interval: 25,
};
const route = {
  route_id: 2,
  geometry: [
    [0, 0],
    [1, 0],
    [3, 0],
  ],
  distance_miles: 100,
  duration_seconds: 7200,
  checkpoints: [{ mile: 0 }, { mile: 25 }, { mile: 100 }],
  risk_miles: { Low: 90, Severe: 10, High: 0, "No Travel": 0 },
  average_risk: 0.3,
};
const response = {
  routes: [route],
  ranking: [{ route_id: 2, ...route }],
  excluded_routes: [],
  recommended_route_id: 2,
};
const mockResponse = (value, ok = true) =>
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok, status: 502, json: async () => value }),
  );
describe("trip planning", () => {
  it("validates inputs and preserves explicit UTC", () => {
    expect(validateTrip(trip).departure_time).toBe(trip.departure_time);
    for (const patch of [
      { origin: " " },
      { load_weight: -1 },
      { departure_time: "bad" },
      { checkpoint_interval: 12 },
      { departure_time: "2020-01-01" },
    ])
      expect(() => validateTrip({ ...trip, ...patch })).toThrow();
  });
  it("merges backend summaries", async () => {
    mockResponse(response);
    expect((await planTrip(trip)).routes[0].average_risk).toBe(0.3);
  });
  it("loads encoded city and country suggestions", async () => {
    mockResponse([{ label: "Lahore, Punjab, Pakistan" }]);
    await expect(searchLocations("Lahore, PK")).resolves.toEqual([
      { label: "Lahore, Punjab, Pakistan" },
    ]);
    expect(fetch).toHaveBeenCalledWith(
      "/api/locations/?q=Lahore%2C%20PK",
      expect.objectContaining({ signal: undefined }),
    );
  });
  it("checks routing coverage for selected coordinates", async () => {
    mockResponse({ covered: false });
    await expect(checkLocationCoverage(31.558, 74.35071)).resolves.toBe(false);
    expect(fetch).toHaveBeenCalledWith(
      "/api/coverage/?lat=31.558&lon=74.35071",
      { signal: undefined },
    );
  });
  it("rejects malformed and empty route data", async () => {
    for (const value of [
      null,
      { routes: [] },
      {
        routes: [
          {
            ...route,
            geometry: [
              [200, 0],
              [0, 0],
            ],
          },
        ],
      },
    ]) {
      mockResponse(value);
      await expect(planTrip(trip)).rejects.toThrow();
    }
  });
  it("handles non JSON failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: async () => {
          throw Error();
        },
      }),
    );
    await expect(planTrip(trip)).rejects.toThrow("502");
  });
  it("renders recommendation and selects a route", () => {
    const select = vi.fn();
    render(<RouteCard route={route} recommended selected onSelect={select} />);
    fireEvent.click(screen.getByRole("button"));
    expect(select).toHaveBeenCalled();
    expect(screen.getByText("Recommended")).toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
  it("labels excluded routes", () => {
    render(
      <RouteCard route={{ ...route, contains_no_travel: true }} recommended />,
    );
    expect(screen.getByText("No Travel - excluded")).toBeInTheDocument();
    expect(screen.queryByText("Recommended")).not.toBeInTheDocument();
  });
  it("selects forecast hour and steps", () => {
    const setHour = vi.fn();
    render(<ForecastTimeline times={[]} hour={12} setHour={setHour} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "36" } });
    expect(setHour).toHaveBeenCalledWith(36);
    fireEvent.click(screen.getByLabelText("Next hour"));
    expect(setHour).toHaveBeenCalledWith(13);
  });
  it("submits form with sample values", () => {
    const submit = vi.fn();
    render(<TripForm onSubmit={submit} />);
    fireEvent.click(screen.getByText("Find safest route"));
    expect(submit).toHaveBeenCalledWith(
      expect.objectContaining({
        origin: "Chicago, Illinois, USA",
        origin_lat: 41.8781,
        origin_lon: -87.6298,
      }),
    );
  });
  it("selects backend recommendation and retains results on failure", async () => {
    mockResponse(response);
    render(<App />);
    fireEvent.click(screen.getByText("Find safest route"));
    expect(await screen.findByText("Route 2 ranks first")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Route 2\s*Recommended/ }),
    ).toHaveAttribute("aria-pressed", "true");
    mockResponse({ error: "Weather unavailable" }, false);
    fireEvent.click(screen.getByText("Find safest route"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Weather unavailable",
    );
    expect(screen.getByText("Route 2 ranks first")).toBeInTheDocument();
  });
  it("warns when recommendation is unavailable", async () => {
    mockResponse({ ...response, recommended_route_id: null });
    render(<App />);
    fireEvent.click(screen.getByText("Find safest route"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No route can be recommended",
    );
  });
});
describe("geospatial risk", () => {
  it("uses consistent risk colors and worse endpoint", () => {
    expect(Object.keys(riskColors)).toContain("No Travel");
    expect(
      segmentRisk(
        { risk: { overall_risk: "Low" } },
        { risk: { overall_risk: "Severe" } },
      ),
    ).toBe("Severe");
    expect(segmentRisk(null, {})).toBe("Unavailable");
  });
  it("splits scaled physical distance rather than coordinate indices", () => {
    const pieces = splitRoute(route);
    expect(pieces[0].at(-1)[0]).toBeCloseTo(0.75, 4);
    expect(pieces[1].at(-1)).toEqual([3, 0]);
  });
  it("selects actual hourly data and exposes missing hours", () => {
    const cp = { hourly_forecast: [{ risk: { overall_risk: "Low" } }, null] };
    expect(conditionsAt(cp, "forecast", 0).risk.overall_risk).toBe("Low");
    expect(conditionsAt(cp, "forecast", 1)).toBeNull();
  });
});
