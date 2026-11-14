import polyline
from datetime import datetime, timezone, timedelta

from routing.geometry import generate_check_points
from routing.eta import calculate_checkpoint_etas
from routing.weather import get_hourly_weather_many, get_weather_at_eta
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

    base_time = datetime.fromisoformat(departure_time).astimezone(timezone.utc)
    base_time = base_time.replace(minute=0, second=0, microsecond=0) + (timedelta(hours=1) if base_time.minute or base_time.second or base_time.microsecond else timedelta())
    forecast_times = [(base_time + timedelta(hours=h)).isoformat() for h in range(49)]
    weather_series = get_hourly_weather_many([
        (checkpoint['lat'], checkpoint['lon'])
        for checkpoint in checkpoints_with_etas
    ])
    for checkpoint, weather_data in zip(checkpoints_with_etas, weather_series):
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

        hourly_forecast = []
        for timestamp in forecast_times:
            try:
                conditions = get_weather_at_eta(weather_data, timestamp)
                hourly_risk = calculate_weather_risk(
                    wind_mph=conditions['wind_mph'], rain_in_per_hr=conditions['rain_in_per_hr'],
                    snow_in_per_hr=conditions['snow_in_per_hr'], load_weight_lb=load_weight_lb)
                hourly_forecast.append({'weather': conditions, 'risk': hourly_risk})
            except ValueError:
                hourly_forecast.append(None)
        results.append({
            **checkpoint,
            "weather": weather,
            "risk": risk,
            "hourly_forecast": hourly_forecast
        })
    return {
        "distance_miles": distance,
        "duration_seconds": duration_seconds,
        "geometry": [
            [lon, lat]
            for lat, lon in coordinates
        ],
        "checkpoints": results,
        "forecast_times": forecast_times
    }
