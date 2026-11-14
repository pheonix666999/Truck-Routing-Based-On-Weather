
import time
import requests

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import TripSerializer
from .geocoding import geocode_location
from .services import get_truck_routes
from .analysis import analyze_route_weather
from .ranking import rank_routes

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"})

@api_view(['POST'])
def plan_trip(request):
    serializer = TripSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    trip = serializer.validated_data

    try:
        origin = geocode_location(trip["origin"])
        # Have to wait to cater for the rate limit
        time.sleep(1.1)
        destination = geocode_location(trip["destination"])
        route_data = get_truck_routes(origin, destination)
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
        return Response(
            {"error": "External routing or weather service failed"},
            status=502
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

