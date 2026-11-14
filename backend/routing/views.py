
import time
import requests
import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import TripSerializer
from .geocoding import geocode_location, search_locations
from .services import get_truck_routes, location_is_covered
from .analysis import analyze_route_weather
from .ranking import rank_routes

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"})


@api_view(['GET'])
def location_search(request):
    query = request.query_params.get("q", "").strip()
    if len(query) < 2:
        return Response([])
    if len(query) > 100:
        return Response({"error": "Search is too long"}, status=400)
    try:
        return Response(search_locations(query))
    except requests.RequestException:
        logger.exception("Location lookup failed")
        return Response(
            {"error": "Location search is temporarily unavailable"},
            status=502,
        )


@api_view(['GET'])
def location_coverage(request):
    try:
        latitude = float(request.query_params.get("lat", ""))
        longitude = float(request.query_params.get("lon", ""))
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            {"error": "Valid latitude and longitude are required"},
            status=400,
        )
    try:
        return Response({"covered": location_is_covered(latitude, longitude)})
    except (requests.RequestException, ValueError):
        logger.exception("Routing coverage check failed")
        return Response(
            {"error": "Routing coverage could not be verified"},
            status=502,
        )


def trip_location(trip, name):
    lat = trip.get(f"{name}_lat")
    lon = trip.get(f"{name}_lon")
    if lat is not None and lon is not None:
        return {"lat": lat, "lon": lon}
    return geocode_location(trip[name])

@api_view(['POST'])
def plan_trip(request):
    serializer = TripSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    trip = serializer.validated_data

    try:
        origin = trip_location(trip, "origin")
        if "origin_lat" not in trip and "destination_lat" not in trip:
            time.sleep(1.1)
        destination = trip_location(trip, "destination")
    except requests.RequestException:
        logger.exception("Location resolution failed")
        return Response(
            {"error": "Location lookup service is unavailable. Select a suggested location and try again."},
            status=502,
        )
    except ValueError as error:
        return Response({"error": str(error)}, status=400)

    try:
        route_data = get_truck_routes(origin, destination)
    except requests.HTTPError as error:
        detail = "Routing service failed"
        error_code = None
        if error.response is not None:
            try:
                provider_error = error.response.json()
                detail = provider_error.get("error", detail)
                error_code = provider_error.get("error_code")
            except ValueError:
                pass
        status = 400 if error.response is not None and error.response.status_code == 400 else 502
        logger.warning("Routing provider returned %s: %s", status, detail)
        code = "ROUTE_NOT_COVERED" if error_code == 171 else "ROUTING_FAILED"
        return Response({"error": detail, "code": code}, status=status)
    except requests.RequestException:
        logger.exception("Routing request failed")
        return Response({"error": "Routing service is unavailable"}, status=502)

    try:
        routes = [route_data["trip"]]
        for alternate in route_data.get("alternates", []):
            routes.append(alternate['trip'])

        analyzed_routes = []

        for index, route in enumerate(routes, start=1):
            analysis = analyze_route_weather(
                route=route,
                departure_time=trip["departure_time"].isoformat(),
                load_weight_lb=trip["load_weight"],
                interval_miles=int(trip["checkpoint_interval"])
            )
            analysis["route_id"] = index
            analyzed_routes.append(analysis)
        ranking = rank_routes(analyzed_routes)
    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=400
        )
    except requests.RequestException:
        logger.exception("Weather request failed")
        return Response(
            {"error": "Weather service is unavailable"},
            status=502
        )
    except (KeyError, TypeError, IndexError):
        logger.exception("External service returned invalid route or weather data")
        return Response(
            {"error": "An external service returned invalid data"},
            status=502,
        )
    except Exception:
        logger.exception("Unexpected trip planning failure")
        return Response(
            {"error": "The trip could not be processed"},
            status=500,
        )
    recommended = ranking['recommended_route']

    recommended_id = (
        recommended["route_id"]
        if recommended is not None
        else None
    )

    return Response({
        "recommended_route_id": recommended_id,
        "routes": analyzed_routes,
        "ranking": ranking["ranked_routes"],
        "excluded_routes": ranking["excluded_routes"]
    })

