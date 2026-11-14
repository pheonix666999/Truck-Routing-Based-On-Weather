
import os
import django

from datetime import datetime, timedelta, timezone

# Initialize Django before accessing services.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from routing.services import get_truck_routes
from routing.analysis import analyze_route_weather


def test_route_analysis():

    # Fetch routes from Valhalla.
    data = get_truck_routes()

    # Use only the primary route for this test.
    route = data["trip"]

    # Depart one hour from now.
    departure = datetime.now(timezone.utc) + timedelta(hours=1)

    # Analyze the route with a 42,000 lb load.
    result = analyze_route_weather(
        route=route,
        departure_time=departure.isoformat(),
        load_weight_lb=42000,
        interval_miles=25
    )

    print("\nROUTE WEATHER RISK ANALYSIS")
    print("-" * 65)

    print(f"Route distance: {result['distance_miles']:.2f} miles")
    print(f"Total checkpoints: {len(result['checkpoints'])}")

    for checkpoint in result["checkpoints"]:

        weather = checkpoint["weather"]
        risk = checkpoint["risk"]

        print(
            f"Mile {checkpoint['mile']:6.2f} | "
            f"Wind {weather['wind_mph']:5.1f} mph | "
            f"Rain {weather['rain_in_per_hr']:.3f} | "
            f"Snow {weather['snow_in_per_hr']:.3f} | "
            f"Risk: {risk['overall_risk']}"
        )

    print("-" * 65)
    print("SUCCESS: Route weather analysis completed!")


if __name__ == "__main__":
    test_route_analysis()
