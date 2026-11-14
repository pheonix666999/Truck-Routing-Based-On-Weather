
import os
import django
import polyline

from datetime import datetime, timedelta, timezone

# STEP 1: Initialize Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

# Import our existing functions
from routing.services import get_truck_routes
from routing.geometry import generate_check_points
from routing.eta import calculate_checkpoint_etas
from routing.weather import get_hourly_weather, get_weather_at_eta


def test_live_weather():

    # STEP 2: Fetch actual truck routes
    data = get_truck_routes()

    # For now, use only the primary route
    route = data["trip"]

    distance = route["summary"]["length"]
    duration = route["summary"]["time"]

    # STEP 3: Decode the route's GPS coordinates
    coordinates = []

    for leg in route["legs"]:
        leg_coordinates = polyline.decode(
            leg["shape"],
            precision=6
        )

        if coordinates:
            leg_coordinates = leg_coordinates[1:]

        coordinates.extend(leg_coordinates)

    # STEP 4: Generate checkpoints every 25 miles
    checkpoints = generate_check_points(
        coordinates=coordinates,
        interval_miles=25,
        route_distance_miles=distance
    )

    # STEP 5: Set departure one hour from now
    # This keeps our test inside the forecast window.
    departure = datetime.now(timezone.utc) + timedelta(hours=1)

    # STEP 6: Calculate arrival times
    checkpoints_with_etas = calculate_checkpoint_etas(
        checkpoints=checkpoints,
        departure_time=departure.isoformat(),
        route_duration_seconds=duration,
        route_distance_miles=distance
    )

    # STEP 7: Select the checkpoint at mile 25
    checkpoint = checkpoints_with_etas[1]

    latitude = checkpoint["lat"]
    longitude = checkpoint["lon"]
    eta = checkpoint["eta"]

    # STEP 8: Get the weather forecast for this location
    weather_data = get_hourly_weather(
        latitude,
        longitude
    )

    # Check units before using weather risk thresholds
    units = weather_data["hourly_units"]

    if units["snowfall"] != "inch":
        raise ValueError("Snowfall must be in inches")

    # STEP 9: Match forecast to arrival time
    weather = get_weather_at_eta(
        weather_data,
        eta
    )

    # STEP 10: Display the results
    print("\nLIVE WEATHER CHECKPOINT TEST")
    print("-" * 45)

    print(f"Route distance: {distance:.2f} miles")
    print(f"Checkpoint: Mile {checkpoint['mile']:.0f}")
    print(f"Latitude: {latitude:.6f}")
    print(f"Longitude: {longitude:.6f}")
    print(f"Truck ETA: {eta}")

    print("-" * 45)

    print(f"Forecast time: {weather['forecast_time']}")
    print(f"Wind: {weather['wind_mph']} mph")
    print(f"Rain: {weather['rain_in_per_hr']:.3f} in/hr")
    print(f"Snow: {weather['snow_in_per_hr']:.3f} in/hr")

    print("-" * 45)
    print("SUCCESS: Real checkpoint weather retrieved!")


if __name__ == "__main__":
    test_live_weather()
