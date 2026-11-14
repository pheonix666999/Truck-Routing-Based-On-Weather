# Haversine Line Formula

from math import radians, sin, cos, sqrt, asin

EARTH_RADIUS_MILES = 3958.76

def distance_miles(point_a, point_b):
    lat1, lon1 = point_a
    lat2, lon2 = point_b

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * asin(min(1, sqrt(a)))
    return EARTH_RADIUS_MILES * c

def generate_check_points(coordinates, interval_miles, route_distance_miles):
    if interval_miles not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25 or 50 miles")

    if len(coordinates) < 2 or route_distance_miles <= 0:
        raise ValueError("Invalid route geometry or distance")
    
    segment_lengths = []

    for i in range(len(coordinates) - 1):
        length = distance_miles(coordinates[i], coordinates[i + 1])
        segment_lengths.append(length)

    geometry_total = sum(segment_lengths)

    if geometry_total <= 0:
        raise ValueError("Route geometry has no distance")

    scale = route_distance_miles / geometry_total

    checkpoints = [
        {
            "mile": 0.0,
            "lat": coordinates[0][0],
            "lon": coordinates[0][1]
        }
    ]

    next_mile = interval_miles

    accumulated = 0.0

    for i, raw_length in enumerate(segment_lengths):
        segment_length = raw_length * scale
        if segment_length <= 0:
            continue
        segment_end = accumulated + segment_length
        while (next_mile < route_distance_miles and next_mile <= segment_end + 1e-9):
            fraction = (
                (next_mile - accumulated) / segment_length
            )
            fraction = max(0.0, min(1.0, fraction))

            start_lat, start_lon = coordinates[i]
            end_lat, end_lon = coordinates[i + 1]

            lat = start_lat + fraction * (end_lat - start_lat)
            lon = start_lon + fraction * (end_lon - start_lon)

            checkpoints.append(
                {
                    "mile": float(next_mile),
                    "lat": lat,
                    "lon": lon
                }
            )

            next_mile += interval_miles
        accumulated = segment_end
    checkpoints.append(
        {
            "mile": route_distance_miles,
            "lat": coordinates[-1][0],
            "lon": coordinates[-1][1]

        }
    )
    return checkpoints