from datetime import datetime, timedelta

def calculate_checkpoint_etas(
        checkpoints,
        departure_time,
        route_duration_seconds,
        route_distance_miles
):
    departure = datetime.fromisoformat(departure_time)
    if departure.utcoffset() is None:
        raise ValueError("Departure time must include a timezone")
    if route_distance_miles <= 0 or route_duration_seconds < 0:
        raise ValueError("Invalid route distance or duration")
    results = []
    for checkpoint in checkpoints:
        fraction = checkpoint["mile"] / route_distance_miles
        elapsed_second = fraction * route_duration_seconds
        arrival = departure + timedelta(seconds=elapsed_second)
        results.append({
            **checkpoint,
            "eta": arrival.isoformat()
        })
    return results