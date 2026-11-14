
from routing.weather import get_hourly_weather


def test_weather():

    # Chicago — our first route's starting checkpoint
    latitude = 41.878101
    longitude = -87.629771

    # Request weather forecast data
    data = get_hourly_weather(latitude, longitude)

    # Extract hourly forecasts and their units
    hourly = data["hourly"]
    units = data["hourly_units"]

    print("WEATHER FORECAST TEST")
    print("-" * 45)

    print("Units:")
    print(units)

    # Print the first five forecast hours
    for i in range(5):

        wind = hourly["wind_speed_10m"][i]
        rain = hourly["rain"][i]
        showers = hourly["showers"][i]
        snow = hourly["snowfall"][i]
        time = hourly["time"][i]

        print(f"\nTime: {time}")
        print(f"Wind: {wind} mph")
        print(f"Rain + showers: {rain + showers:.3f} in/hr")
        print(f"Snow: {snow} in/hr")


if __name__ == "__main__":
    test_weather()
