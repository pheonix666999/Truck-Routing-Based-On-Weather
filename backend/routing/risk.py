RISK_LEVELS = {
    "Low": 0,
    "Moderate": 1,
    "High": 2,
    "Severe": 3,
    "No Travel": 4
}

def calculate_weather_risk(
    wind_mph,
    rain_in_per_hr,
    snow_in_per_hr,
    load_weight_lb
):
    if any(value < 0 for value in (
        wind_mph,
        rain_in_per_hr,
        snow_in_per_hr,
        load_weight_lb

    )):
        raise ValueError("Weather and load values cannot be negative")


    # Wind
    if wind_mph >= 55:
        wind_risk = "No Travel"

    elif wind_mph >= 45 and load_weight_lb > 30000:
        wind_risk = "No Travel"

    elif wind_mph >= 45:
        wind_risk = "Severe"

    elif wind_mph >= 35 and load_weight_lb > 40000:
        wind_risk = "Severe"

    elif wind_mph >= 35:
        wind_risk = "High"

    elif wind_mph >= 25:
        wind_risk = "Moderate"
    else:
        wind_risk = "Low"

    # Rain
    if rain_in_per_hr > 1.0:
        rain_risk = "No Travel"
    elif rain_in_per_hr >= 0.50:
        rain_risk = "Severe"
    elif rain_in_per_hr >= 0.25:
        rain_risk = "High"
    elif rain_in_per_hr >= 0.10:
        rain_risk = "Moderate"
    else:
        rain_risk = "Low"

    # Snowfall
    if snow_in_per_hr > 3.0:
        snow_risk = "No Travel"
    elif snow_in_per_hr >= 2.0:
        snow_risk = "Severe"
    elif snow_in_per_hr >= 1.0:
        snow_risk = "High"
    elif snow_in_per_hr >= 0.5:
        snow_risk = "Moderate"
    else:
        snow_risk = "Low"

    overall_risk = max(
        wind_risk,
        rain_risk,
        snow_risk,
        key=lambda risk: RISK_LEVELS[risk]
    )

    return {
        "wind_risk": wind_risk,
        "rain_risk": rain_risk,
        "snow_risk": snow_risk,
        "overall_risk": overall_risk
    }
