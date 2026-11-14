import requests
from django.conf import settings

def get_truck_routes(origin, destination):
    url = "https://api.simplerouting.io/valhalla/route"

    headers = {
        "Authorization": f"Bearer {settings.SIMPLE_ROUTING_API_KEY}"
    }

    payload = {
        "locations": [
            origin,
            destination
        ],
        "costing": "truck",
        "units": "miles",
        "alternates": 2
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()