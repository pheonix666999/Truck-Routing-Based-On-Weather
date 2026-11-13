
import os
import django
import polyline
from unittest.mock import patch

# Initialize Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from routing.services import get_truck_routes
from routing.geometry import distance_miles, generate_check_points


# ==========================================================
# TEST 1: OUR 32-MILE MATHEMATICAL EXAMPLE
# ==========================================================

def test_example_route():

    print("\nTESTING OUR 32-MILE EXAMPLE")
    print("=" * 45)

    # The five example GPS points: A, B, C, D, E
    #
    # B, C, D and E use the illustrative coordinates
    # from our earlier calculations.
    #
    # A is an additional illustrative starting point.

    coordinates = [
        (40.940, -87.080),  # A - mile 0
        (41.000, -87.000),  # B - mile 6.4
        (41.080, -86.900),  # C - mile 14.9333
        (41.160, -86.800),  # D - mile 23.4667
        (41.240, -86.700),  # E - mile 32
    ]

    # These are the segment distances from our example.
    #
    # A -> B = 6 miles
    # B -> C = 8 miles
    # C -> D = 8 miles
    # D -> E = 8 miles
    #
    # Total geometry distance = 30 miles

    example_segment_lengths = [6.0, 8.0, 8.0, 8.0]

    # API reports 32 miles, so:
    #
    # scale = 32 / 30 = 1.0666667

    route_distance = 32.0
    checkpoint_interval = 10

    print(f"Geometry distance: {sum(example_segment_lengths)} miles")
    print(f"API distance: {route_distance} miles")
    print(f"Scale: {route_distance / sum(example_segment_lengths):.7f}")
    print(f"Checkpoint interval: {checkpoint_interval} miles")

    # IMPORTANT:
    #
    # Our example GPS coordinates are illustrative.
    # Their real Haversine distances do not equal
    # exactly 6, 8, 8 and 8 miles.
    #
    # patch() temporarily makes distance_miles()
    # return our example distances instead.
    #
    # This lets us test the exact calculations
    # we worked through together.

    with patch(
        "routing.geometry.distance_miles",
        side_effect=example_segment_lengths
    ):

        checkpoints = generate_check_points(
            coordinates=coordinates,
            interval_miles=checkpoint_interval,
            route_distance_miles=route_distance
        )

    print("\nEXPECTED CHECKPOINT MILES:")
    print([0, 10, 20, 30, 32])

    # Your function is currently incomplete.
    if checkpoints is None:
        print("\nFunction is not finished yet.")
        print("Complete generate_check_points() and return checkpoints.")
        return

    print("\nACTUAL CHECKPOINTS:")
    print("-" * 45)

    for checkpoint in checkpoints:
        print(
            f"Mile: {checkpoint['mile']:.2f} | "
            f"Lat: {checkpoint['lat']:.7f} | "
            f"Lon: {checkpoint['lon']:.7f}"
        )

    # Check whether the function returned
    # the correct checkpoint distances.

    expected_miles = [0, 10, 20, 30, 32]
    actual_miles = [point["mile"] for point in checkpoints]

    assert actual_miles == expected_miles, (
        f"Expected {expected_miles}, got {actual_miles}"
    )

    # Check the GPS positions calculated in our example.
    expected_positions = [
        (40.9400000, -87.0800000),
        (41.0337500, -86.9578125),
        (41.1275000, -86.8406250),
        (41.2212500, -86.7234375),
        (41.2400000, -86.7000000),
    ]

    for checkpoint, expected in zip(checkpoints, expected_positions):
        assert abs(checkpoint["lat"] - expected[0]) < 0.000001
        assert abs(checkpoint["lon"] - expected[1]) < 0.000001

    print("\nSUCCESS: All example checkpoints are correct!")


# ==========================================================
# TEST 2: REAL ROUTES FROM VALHALLA API
# ==========================================================

def test_routes():

    data = get_truck_routes()

    routes = [data["trip"]]

    for alternate in data.get("alternates", []):
        routes.append(alternate["trip"])

    print(f"\nTotal routes found: {len(routes)}")
    print("-" * 40)

    for index, route in enumerate(routes, start=1):

        summary = route["summary"]

        distance = summary["length"]
        duration_minutes = summary["time"] / 60

        # Decode GPS coordinates from every route leg
        coordinates = []

        for leg in route["legs"]:
            leg_coordinates = polyline.decode(
                leg["shape"],
                precision=6
            )

            if coordinates:
                leg_coordinates = leg_coordinates[1:]

            coordinates.extend(leg_coordinates)

        # Calculate total geometry distance
        geometry_distance = 0

        for i in range(len(coordinates) - 1):
            geometry_distance += distance_miles(
                coordinates[i],
                coordinates[i + 1]
            )

        print(f"\nRoute {index}")
        print(f"API distance: {distance:.2f} miles")
        print(f"Calculated distance: {geometry_distance:.2f} miles")
        print(f"Duration: {duration_minutes:.1f} minutes")
        print(f"Total GPS points: {len(coordinates)}")

        # Generate real checkpoints
        checkpoints = generate_check_points(
            coordinates=coordinates,
            interval_miles=25,
            route_distance_miles=distance
        )

        if checkpoints is None:
            print("Checkpoint function is incomplete.")
        else:
            print(f"Total checkpoints: {len(checkpoints)}")

            for checkpoint in checkpoints:
                print(
                    f"Mile: {checkpoint['mile']:.2f} | "
                    f"Lat: {checkpoint['lat']:.6f} | "
                    f"Lon: {checkpoint['lon']:.6f}"
                )

        print("-" * 40)


# ==========================================================
# CHOOSE WHICH TEST TO RUN
# ==========================================================

if __name__ == "__main__":

    # Run our mathematical example
    test_example_route()

    # Uncomment this when you want to test real API routes
    # test_routes()
