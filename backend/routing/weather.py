import requests
from datetime import datetime, timezone, timedelta
from django.core.cache import cache
from .http import request

def weather_cache_key(latitude, longitude):
    return f"weather:{latitude:.4f}:{longitude:.4f}"


def get_hourly_weather(latitude, longitude):
    return get_hourly_weather_many([(latitude, longitude)])[0]


def get_hourly_weather_many(points):
    results = [cache.get(weather_cache_key(*point)) for point in points]
    missing = [index for index, result in enumerate(results) if result is None]
    if not missing:
        return results

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": ",".join(str(points[index][0]) for index in missing),
        "longitude": ",".join(str(points[index][1]) for index in missing),
        "hourly": (
            "wind_speed_10m,"
            "rain,"
            "showers,"
            "snowfall"
        ),
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "forecast_days": 7
    }
    response = request(
        "GET",
        url,
        params=params,
        timeout=15
    )
    response.raise_for_status()
    payload = response.json()
    forecasts = payload if isinstance(payload, list) else [payload]
    if len(forecasts) != len(missing):
        raise ValueError("Weather service returned incomplete location data")
    for index, forecast in zip(missing, forecasts):
        results[index] = forecast
        cache.set(weather_cache_key(*points[index]), forecast, 900)
    return results

def get_weather_at_eta(weather_data, eta_string):
    eta = datetime.fromisoformat(eta_string)
    if eta.utcoffset() is None:
            raise ValueError("ETA must contain a timezone")
    eta_utc = eta.astimezone(timezone.utc)
    hourly = weather_data['hourly']
    if not hourly.get('time') or eta_utc < datetime.fromisoformat(hourly['time'][0]).replace(tzinfo=timezone.utc):
        raise ValueError("ETA is before available forecast coverage")

    for i, time_string in enumerate(hourly["time"]):
        forecast_time = datetime.fromisoformat(
            time_string
        ).replace(tzinfo=timezone.utc)
        if forecast_time >= eta_utc:
            if forecast_time - eta_utc >= timedelta(hours=1):
                raise ValueError("Missing hourly forecast period")
            wind = hourly["wind_speed_10m"][i]
            rain = hourly["rain"][i]
            showers = hourly["showers"][i]
            snow = hourly["snowfall"][i]
            # Open-Meteo can report snowfall in cm even when rain is in inches.
            if snow is not None and weather_data.get("hourly_units", {}).get("snowfall") == "cm":
                snow /= 2.54
            if any(value is None for value in
                    (wind, rain, showers, snow)):
                raise ValueError("Missing weather data")

            return {
                "forecast_time": forecast_time.isoformat(),
                "wind_mph": wind,
                "rain_in_per_hr": rain + showers,
                "snow_in_per_hr": snow
            }
    raise ValueError("No weather forecast available for ETA")
