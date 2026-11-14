import requests
from django.conf import settings
from django.core.cache import cache
from .http import request


def geocode_location(location):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "jsonv2",
        "limit": 1
    }

    if not settings.NOMINATIM_USER_AGENT:
        raise ValueError("Nominatim User-Agent is not configured")

    response = request(
        "GET",
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


def search_locations(query):
    cache_key = f"location-search:{query.casefold()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    response = request(
        "GET",
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": query,
            "count": 6,
            "language": "en",
            "format": "json",
        },
        timeout=4,
        retries=0,
    )
    response.raise_for_status()

    locations = []
    seen = set()
    for result in response.json().get("results", []):
        label = ", ".join(dict.fromkeys(filter(None, (
            result.get("name"),
            result.get("admin1"),
            result.get("country"),
        ))))
        if label and label not in seen:
            seen.add(label)
            locations.append({
                "label": label,
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
            })

    cache.set(cache_key, locations, 3600)
    return locations
