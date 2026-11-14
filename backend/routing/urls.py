from django.urls import path
from .views import health_check, location_coverage, location_search, plan_trip

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('locations/', location_search, name='location_search'),
    path('coverage/', location_coverage, name='location_coverage'),
    path('plan/', plan_trip, name='plan_trip')
]
