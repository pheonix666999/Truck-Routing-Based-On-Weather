
from routing.weather import get_weather_at_eta


def test_weather_eta():

    # Simulated Open-Meteo response
    weather_data = {
        "hourly": {
            "time": [
                "2026-11-15T14:00",
                "2026-11-15T15:00",
                "2026-11-15T16:00"
            ],
            "wind_speed_10m": [12.0, 36.0, 40.0],
            "rain": [0.00, 0.15, 0.10],
            "showers": [0.00, 0.05, 0.05],
            "snowfall": [0.00, 0.00, 0.00]
        }
    }

    # The truck arrives at 08:20 UTC-6.
    # This is equivalent to 14:20 UTC.
    eta = "2026-11-15T08:20:00-06:00"

    result = get_weather_at_eta(weather_data, eta)

    print("Matched forecast:", result["forecast_time"])
    print("Wind:", result["wind_mph"], "mph")
    print("Rain:", result["rain_in_per_hr"], "in/hr")
    print("Snow:", result["snow_in_per_hr"], "in/hr")

    # Verify that we selected the 15:00 UTC forecast.
    assert result["forecast_time"] == (
        "2026-11-15T15:00:00+00:00"
    )

    assert result["wind_mph"] == 36.0
    assert abs(result["rain_in_per_hr"] - 0.20) < 0.000001
    assert result["snow_in_per_hr"] == 0.0

    print("SUCCESS: Weather matched to checkpoint ETA!")


if __name__ == "__main__":
    test_weather_eta()
