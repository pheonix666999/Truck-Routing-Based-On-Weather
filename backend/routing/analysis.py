import polyline

from routing.geometry import generate_check_points
from routing.eta import calculate_checkpoint_etas
from routing.weather import get_hourly_weather, get_weather_at_eta
from routing.risk import calculate_weather_risk

def analyze_route_weather(
    route,
    departure_time,
    load_weight_lb,
    interval_miles=25
):
    summary = route['summary']

    distance = summary['length']
    duration_seconds = summary['time']

    coordinates = []

    for leg in route["legs"]:
        points = polyline.decode(
            leg['shape'],
            precision=6
        )
        if coordinates and points and coordinates[-1] == points[0]:
            points = points[1:]

        coordinates.extend(points)

    checkpoints = generate_check_points(
        coordinates=coordinates,
        interval_miles=interval_miles,
        route_distance_miles=distance
    )

    checkpoints_with_etas = calculate_checkpoint_etas(
        checkpoints=checkpoints,
        departure_time=departure_time,
        route_duration_seconds=duration_seconds,
        route_distance_miles=distance
    )
    
    results = []

    for checkpoint in checkpoints_with_etas:
        weather_data = get_hourly_weather(
            checkpoint['lat'],
            checkpoint['lon']
        )
        weather = get_weather_at_eta(
            weather_data,
            checkpoint['eta']
        )

        risk = calculate_weather_risk(
            wind_mph=weather["wind_mph"],
            rain_in_per_hr=weather["rain_in_per_hr"],
            snow_in_per_hr=weather["snow_in_per_hr"],
            load_weight_lb=load_weight_lb
        )

        results.append({
            **checkpoint,
            "weather": weather,
            "risk": risk
        })
    return {
        "distance_miles": distance,
        "duration_seconds": duration_seconds,
        "geometry": [
            [lon, lat]
            for lat, lon in coordinates
        ],
        "checkpoints": results
    }
