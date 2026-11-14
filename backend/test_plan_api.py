"""Integration test for the Weather Routing POST /api/plan/ endpoint.

Place this file in the Django backend folder, beside manage.py, then run:
    python test_plan_api.py

Uses Django REST Framework's APIClient, so no separate runserver is necessary.
Calls the real geocoding, routing, and weather providers.
"""

import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from rest_framework.test import APIClient  # noqa: E402


def test_plan_api():
    client = APIClient(HTTP_HOST="localhost")
    payload = {
        "origin": "Chicago, Illinois, USA",
        "destination": "Detroit, Michigan, USA",
        "departure_time": (
            datetime.now(timezone.utc) + timedelta(hours=2)
        ).isoformat(),
        "load_weight": "42000.50",
        "checkpoint_interval": 25,
    }

    print("Testing POST /api/plan/ ...")
    print("Origin:", payload["origin"])
    print("Destination:", payload["destination"])

    # APIClient runs the Django view directly: no server or PowerShell request needed.
    response = client.post("/api/plan/", data=payload, format="json")
    data = response.json()

    print("HTTP status:", response.status_code)
    if response.status_code != 200:
        print("API response:", data)
        raise AssertionError(f"Expected HTTP 200, got {response.status_code}")

    assert "routes" in data, "Response is missing 'routes'"
    assert "recommended_route_id" in data, "Missing recommended_route_id"
    assert "ranking" in data, "Response is missing 'ranking'"
    assert "excluded_routes" in data, "Missing excluded_routes"
    assert len(data["routes"]) >= 1, "No routes returned"

    print("\nROUTE ANALYSIS RESULTS")
    print("-" * 65)

    for route in data["routes"]:
        checkpoints = route["checkpoints"]
        geometry = route["geometry"]

        assert len(checkpoints) >= 2, "Route needs at least two checkpoints"
        assert len(geometry) >= 2, "Route is missing map geometry"
        assert all("weather" in cp and "risk" in cp for cp in checkpoints)
        assert all("eta" in cp for cp in checkpoints)
        assert abs(checkpoints[-1]["mile"] - route["distance_miles"]) < 0.01

        print(
            f"Route {route['route_id']}: "
            f"{route['distance_miles']:.2f} miles | "
            f"{len(checkpoints)} checkpoints | "
            f"{len(geometry)} GPS points"
        )

    print("\nRANKING")
    for position, route in enumerate(data["ranking"], start=1):
        risk_miles = route["risk_miles"]
        print(
            f"Rank {position}: Route {route['route_id']} | "
            f"Severe {risk_miles['Severe']:.1f} mi | "
            f"High {risk_miles['High']:.1f} mi | "
            f"Average risk {route['average_risk']:.2f}"
        )

    for route in data["excluded_routes"]:
        print(f"Excluded Route {route['route_id']}: No Travel weather")

    recommendation = data["recommended_route_id"]
    print("\nRecommended route:", recommendation if recommendation is not None else "None (No Travel on all routes)")

    if data["ranking"]:
        assert recommendation == data["ranking"][0]["route_id"]
    else:
        assert recommendation is None

    print("\nSUCCESS: The complete /api/plan/ pipeline works!")


if __name__ == "__main__":
    test_plan_api()
