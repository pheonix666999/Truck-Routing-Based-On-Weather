import requests
from datetime import datetime, timezone

def get_hourly_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "wind_speed_10m,"
            "rain,"
            "showers,"
            "snowfall"
        ),
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "forecast_days": 3
    }
    response = requests.get(
        url,
        params=params,
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return data

def get_weather_at_eta(weather_data, eta_string):
    eta = datetime.fromisoformat(eta_string)
    if eta.utcoffset() is None:
            raise ValueError("ETA must contain a timezone")
    eta_utc = eta.astimezone(timezone.utc)
    hourly = weather_data['hourly']

    for i, time_string in enumerate(hourly["time"]):
        forecast_time = datetime.fromisoformat(
            time_string
        ).replace(tzinfo=timezone.utc)
        if forecast_time >= eta_utc:
            wind = hourly["wind_speed_10m"][i]
            rain = hourly["rain"][i]
            showers = hourly["showers"][i]
            snow = hourly["snowfall"][i]
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
