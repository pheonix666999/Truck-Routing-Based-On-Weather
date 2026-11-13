from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TripSerializer

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"})

@api_view(['POST'])
def plan_trip(request):
    serializer = TripSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.data)

    return Response(serializer.errors, status=400)