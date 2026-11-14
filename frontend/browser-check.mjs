// Browser QA only: synthetic routes and blank base style isolate rendering from external APIs.
import { chromium, expect } from "@playwright/test";
const browser = await chromium.launch({
  headless: true,
  channel: process.env.BROWSER_CHANNEL || "chrome",
});
const page = await browser.newPage();
const errors = [];
page.on("console", (m) => {
  if (m.type() === "warning" || m.type() === "error") console.log(m.text());
});
page.on("pageerror", (e) => errors.push(e.message));
const risk = (level) => ({
  overall_risk: level,
  wind_risk: level,
  rain_risk: "Low",
  snow_risk: "Low",
});
const weather = {
  forecast_time: "2026-11-15T14:00:00Z",
  wind_mph: 12,
  rain_in_per_hr: 0,
  snow_in_per_hr: 0,
};
const route = {
  route_id: 1,
  distance_miles: 100,
  duration_seconds: 7200,
  geometry: [
    [-87.6, 41.8],
    [-86.5, 42],
    [-85.5, 42.3],
  ],
  checkpoints: [
    { mile: 0, lon: -87.6, lat: 41.8 },
    { mile: 100, lon: -85.5, lat: 42.3 },
  ].map((c) => ({
    ...c,
    eta: "2026-11-15T14:00:00Z",
    weather,
    risk: risk("Low"),
    hourly_forecast: Array.from({ length: 49 }, (_, h) => ({
      weather,
      risk: risk(h < 24 ? "Low" : "Severe"),
    })),
  })),
  forecast_times: Array.from({ length: 49 }, (_, h) =>
    new Date(Date.UTC(2026, 10, 15, 14 + h)).toISOString(),
  ),
};
const summary = {
  route_id: 1,
  risk_miles: { Low: 100, Moderate: 0, High: 0, Severe: 0, "No Travel": 0 },
  average_risk: 0,
  contains_no_travel: false,
};
await page.route("https://tiles.openfreemap.org/**", (r) =>
  r.fulfill({
    json: {
      version: 8,
      sources: {},
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#e8edf0" },
        },
      ],
    },
  }),
);
let calls = 0;
const planPayloads = [];
let locationCalls = 0;
let coverageCalls = 0;
let coverageResult = true;
await page.route("**/api/locations/**", (r) => {
  locationCalls++;
  return r.fulfill({
    json: [
      {
        label: "Lahore, Punjab, Pakistan",
        latitude: 31.56,
        longitude: 74.35,
      },
    ],
  });
});
await page.route("**/api/coverage/**", (r) => {
  coverageCalls++;
  return r.fulfill({ json: { covered: coverageResult } });
});
await page.route("**/api/plan/", (r) => {
  calls++;
  planPayloads.push(r.request().postDataJSON());
  return r.fulfill({
    json: {
      routes: [route],
      ranking: [summary],
      excluded_routes: [],
      recommended_route_id: 1,
    },
  });
});
for (const viewport of [
  { width: 1920, height: 1080 },
  { width: 1366, height: 768 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 1440, height: 1000 },
  { width: 390, height: 844 },
  { width: 320, height: 568 },
]) {
  await page.setViewportSize(viewport);
  await page.goto("http://127.0.0.1:5173/", {
    waitUntil: "domcontentloaded",
  });
  const origin = page.getByRole("combobox", { name: "Origin" });
  await origin.fill("Lahore");
  await expect(
    page.getByRole("option", { name: "Lahore, Punjab, Pakistan" }),
  ).toBeVisible();
  await page.getByRole("option", { name: "Lahore, Punjab, Pakistan" }).click();
  await expect(origin).toHaveValue("Lahore, Punjab, Pakistan");
  await page.getByRole("button", { name: "Find safest route" }).click();
  await expect(page.getByText("Route 1 ranks first")).toBeVisible();
  await page.getByRole("button", { name: "48h forecast" }).click();
  await page.getByRole("slider", { name: "Forecast hour" }).fill("24");
  await page.getByRole("button", { name: "Mile 0", exact: true }).click();
  await expect(page.locator(".checkpoint-detail")).toContainText("Severe");
  await page.getByRole("button", { name: "Close checkpoint" }).click();
  await page.getByRole("button", { name: "Play forecast" }).click();
  await page.waitForTimeout(1100);
  await page.getByRole("button", { name: "Pause forecast" }).click();
  console.log(
    viewport,
    "overflow:",
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  );
  const clippedControls = await page.evaluate(() =>
    [...document.querySelectorAll("button, input, select")]
      .filter((element) => element.getClientRects().length)
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        return rect.left < -1 || rect.right > innerWidth + 1;
      })
      .map((element) => element.getAttribute("aria-label") || element.textContent),
  );
  if (clippedControls.length)
    throw new Error(`Clipped controls: ${clippedControls.join(", ")}`);
  await page.getByRole("button", { name: "Collapse planning panel" }).click();
  await page.waitForTimeout(100);
  const mapWidths = await page.evaluate(() => ({
    area: document.querySelector(".map-area").getBoundingClientRect().width,
    canvas: document.querySelector(".maplibregl-canvas").getBoundingClientRect()
      .width,
  }));
  if (Math.abs(mapWidths.area - mapWidths.canvas) > 1)
    throw new Error(`Map did not resize: ${JSON.stringify(mapWidths)}`);
  if (viewport.width === 1920)
    await page.screenshot({
      path: `${process.env.TEMP || "/tmp"}/weatherroute-collapsed-1920.png`,
    });
  await page.getByRole("button", { name: "Open planning panel" }).click();
  await page.screenshot({
    path: `${process.env.TEMP || "/tmp"}/weatherroute-${viewport.width}.png`,
    fullPage: true,
  });
}
coverageResult = false;
await page.setViewportSize({ width: 390, height: 844 });
await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
const uncoveredOrigin = page.getByRole("combobox", { name: "Origin" });
await uncoveredOrigin.fill("Lahore");
await expect(
  page.getByRole("option", { name: "Lahore, Punjab, Pakistan" }),
).toBeVisible();
await uncoveredOrigin.press("Tab");
await expect(uncoveredOrigin).toHaveValue("Lahore, Punjab, Pakistan");
await expect(
  page.getByText("This location is not covered by the routing API."),
).toBeVisible();
await expect(
  page.getByRole("button", { name: "Find safest route" }),
).toBeDisabled();
console.log(
  "Plan requests:",
  calls,
  "(expected 7; local slider changes make no requests)",
);
console.log("Location requests:", locationCalls, "(expected 8)");
console.log("Coverage requests:", coverageCalls, "(expected 8)");
console.log("Browser errors:", errors);
await browser.close();
if (
  errors.length ||
  calls !== 7 ||
  locationCalls !== 8 ||
  coverageCalls !== 8 ||
  planPayloads.some(
    (payload) =>
      !Number.isFinite(payload.origin_lat) ||
      !Number.isFinite(payload.destination_lat),
  )
)
  process.exitCode = 1;
