import requests
from django.conf import settings
from django.core.cache import cache
from .http import request


def auth_headers():
    return {"Authorization": f"Bearer {settings.SIMPLE_ROUTING_API_KEY}"}


def location_is_covered(latitude, longitude):
    cache_key = f"route-coverage:{latitude:.4f}:{longitude:.4f}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    response = request(
        "POST",
        "https://api.simplerouting.io/valhalla/locate",
        headers=auth_headers(),
        json={"locations": [{"lat": latitude, "lon": longitude}]},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError("Routing coverage service returned invalid data")
    covered = bool(payload[0].get("edges"))
    cache.set(cache_key, covered, 3600)
    return covered

def get_truck_routes(origin, destination):
    url = "https://api.simplerouting.io/valhalla/route"

    payload = {
        "locations": [
            origin,
            destination
        ],
        "costing": "truck",
        "units": "miles",
        "alternates": 2
    }

    response = request(
        "POST",
        url,
        headers=auth_headers(),
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
