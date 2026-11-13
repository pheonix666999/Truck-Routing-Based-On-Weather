
from unittest.mock import patch

from routing.geometry import generate_check_points
from routing.eta import calculate_checkpoint_etas


def test_example_route():

    # -----------------------------------------
    # STEP 1: Our example GPS coordinates
    # -----------------------------------------

    coordinates = [
        (40.940, -87.080),  # A
        (41.000, -87.000),  # B
        (41.080, -86.900),  # C
        (41.160, -86.800),  # D
        (41.240, -86.700),  # E
    ]

    # GPS distance = 6 + 8 + 8 + 8 = 30 miles
    # API distance = 32 miles
    # Scale = 32 / 30 = 1.0666667

    segment_lengths = [6.0, 8.0, 8.0, 8.0]

    route_distance = 32.0
    interval_miles = 10

    # Departure at 8:00 AM
    departure_time = "2026-11-15T08:00:00-06:00"

    # Total travel time = 64 minutes = 3840 seconds
    route_duration_seconds = 64 * 60

    # -----------------------------------------
    # STEP 2: Generate weather checkpoints
    # -----------------------------------------

    # Replace Haversine distances temporarily
    # with our known example distances.
    with patch(
        "routing.geometry.distance_miles",
        side_effect=segment_lengths
    ):
        checkpoints = generate_check_points(
            coordinates=coordinates,
            interval_miles=interval_miles,
            route_distance_miles=route_distance
        )

    # Expected checkpoint positions
    expected_miles = [0, 10, 20, 30, 32]

    assert [cp["mile"] for cp in checkpoints] == expected_miles

    # Check our calculated GPS coordinates.
    expected_positions = [
        (40.9400000, -87.0800000),
        (41.0337500, -86.9578125),
        (41.1275000, -86.8406250),
        (41.2212500, -86.7234375),
        (41.2400000, -86.7000000),
    ]

    for cp, (lat, lon) in zip(checkpoints, expected_positions):
        assert abs(cp["lat"] - lat) < 0.000001
        assert abs(cp["lon"] - lon) < 0.000001

    # -----------------------------------------
    # STEP 3: Calculate checkpoint ETAs
    # -----------------------------------------

    checkpoints_with_etas = calculate_checkpoint_etas(
        checkpoints=checkpoints,
        departure_time=departure_time,
        route_duration_seconds=route_duration_seconds,
        route_distance_miles=route_distance
    )

    # -----------------------------------------
    # STEP 4: Verify arrival times
    # -----------------------------------------

    expected_times = [
        "08:00:00",
        "08:20:00",
        "08:40:00",
        "09:00:00",
        "09:04:00",
    ]

    actual_times = [
        cp["eta"][11:19]
        for cp in checkpoints_with_etas
    ]

    assert actual_times == expected_times, (
        f"Expected {expected_times}, got {actual_times}"
    )

    # -----------------------------------------
    # STEP 5: Print final results
    # -----------------------------------------

    print("\n32-MILE ROUTE TEST")
    print("-" * 65)

    for cp in checkpoints_with_etas:
        print(
            f"Mile {cp['mile']:5.1f} | "
            f"Lat {cp['lat']:.6f} | "
            f"Lon {cp['lon']:.6f} | "
            f"ETA {cp['eta'][11:19]}"
        )

    print("-" * 65)
    print("SUCCESS: All checkpoints and ETAs are correct!")


if __name__ == "__main__":
    test_example_route()
