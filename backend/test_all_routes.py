
import os
import django
from datetime import datetime, timedelta, timezone

# Initialize Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from routing.services import get_truck_routes
from routing.analysis import analyze_route_weather
from routing.ranking import rank_routes


def test_all_routes():

    # STEP 1: Fetch the primary route and alternatives.
    data = get_truck_routes()

    routes = [data["trip"]]

    for alternate in data.get("alternates", []):
        routes.append(alternate["trip"])

    # STEP 2: Set trip information.
    departure = datetime.now(timezone.utc) + timedelta(hours=1)

    load_weight = 42000
    interval_miles = 25

    # STEP 3: Analyze every route.
    analyzed_routes = []

    for index, route in enumerate(routes, start=1):

        print(f"Analyzing Route {index}...")

        analysis = analyze_route_weather(
            route=route,
            departure_time=departure.isoformat(),
            load_weight_lb=load_weight,
            interval_miles=interval_miles
        )

        # Give each route an ID for ranking.
        analysis["route_id"] = index

        analyzed_routes.append(analysis)

    # STEP 4: Rank all analyzed routes.
    result = rank_routes(analyzed_routes)

    # STEP 5: Display ranking results.
    print("\nREAL ROUTE COMPARISON")
    print("-" * 70)

    for rank, route in enumerate(result["ranked_routes"], start=1):

        print(
            f"Rank {rank} | "
            f"Route {route['route_id']} | "
            f"Distance: {route['distance_miles']:.1f} mi | "
            f"Severe: {route['risk_miles']['Severe']:.1f} mi | "
            f"High: {route['risk_miles']['High']:.1f} mi | "
            f"Avg Risk: {route['average_risk']:.2f}"
        )

    # Show routes with No Travel sections.
    for route in result["excluded_routes"]:
        print(
            f"Route {route['route_id']}: "
            f"NO TRAVEL — {route['risk_miles']['No Travel']:.1f} mi"
        )

    # STEP 6: Display recommendation.
    recommended = result["recommended_route"]

    if recommended is not None:
        print(
            f"\nRECOMMENDED: Route {recommended['route_id']}"
        )
    else:
        print("\nNO SAFE ROUTE AVAILABLE")


if __name__ == "__main__":
    test_all_routes()
