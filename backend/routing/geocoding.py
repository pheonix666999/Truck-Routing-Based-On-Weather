import requests
from django.conf import settings


def geocode_location(location):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "jsonv2",
        "limit": 1
    }

    if not settings.NOMINATIM_USER_AGENT:
        raise ValueError("Nominatim User-Agent is not configured")

    response = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": settings.NOMINATIM_USER_AGENT
        },
        timeout=15
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        raise ValueError(f"Location not found: {location}")

    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"])
    }