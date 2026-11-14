
from routing.risk import calculate_weather_risk


def test_risk():

    # Test 1: All conditions are safe.
    result = calculate_weather_risk(
        wind_mph=8.9,
        rain_in_per_hr=0,
        snow_in_per_hr=0,
        load_weight_lb=42000
    )

    assert result["overall_risk"] == "Low"
    print("PASS: Low-risk weather")

    # Test 2: High wind + heavy load = Severe.
    result = calculate_weather_risk(
        wind_mph=38,
        rain_in_per_hr=0.15,
        snow_in_per_hr=0,
        load_weight_lb=42000
    )

    assert result["overall_risk"] == "Severe"
    print("PASS: Heavy-load wind restriction")

    # Test 3: Wind 48 mph + load over 30,000 lb.
    result = calculate_weather_risk(
        wind_mph=48,
        rain_in_per_hr=0,
        snow_in_per_hr=0,
        load_weight_lb=35000
    )

    assert result["overall_risk"] == "No Travel"
    print("PASS: No Travel for heavy load")

    # Test 4: Wind 55 mph means No Travel for any load.
    result = calculate_weather_risk(
        wind_mph=55,
        rain_in_per_hr=0,
        snow_in_per_hr=0,
        load_weight_lb=1000
    )

    assert result["overall_risk"] == "No Travel"
    print("PASS: Extreme wind restriction")

    # Test 5: Severe rainfall.
    result = calculate_weather_risk(
        wind_mph=10,
        rain_in_per_hr=0.75,
        snow_in_per_hr=0,
        load_weight_lb=20000
    )

    assert result["overall_risk"] == "Severe"
    print("PASS: Severe rainfall")

    # Test 6: Exact 30,000 lb boundary.
    # The load rule says GREATER THAN 30,000 lb.
    result = calculate_weather_risk(
        wind_mph=48,
        rain_in_per_hr=0,
        snow_in_per_hr=0,
        load_weight_lb=30000
    )

    assert result["overall_risk"] == "Severe"
    print("PASS: Load-weight boundary")

    print("\nSUCCESS: All risk tests passed!")


if __name__ == "__main__":
    test_risk()
