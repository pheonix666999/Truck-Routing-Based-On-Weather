from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from django.core.cache import cache
import polyline
import requests
from .analysis import analyze_route_weather
from .weather import get_weather_at_eta, get_hourly_weather, get_hourly_weather_many
from .geocoding import search_locations
from .ranking import rank_routes
from .serializers import TripSerializer
from .views import trip_location
from .http import request
from .services import location_is_covered

class ForecastTests(SimpleTestCase):
    def setUp(self):
        self.base = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
        self.series = {"hourly_units": {"snowfall": "cm"}, "hourly": {
            "time": [(self.base + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(50)],
            "wind_speed_10m": [10]*24 + [60]*26,
            "rain": [0.1]*50, "showers": [0.05]*50, "snowfall": [2.54]*50}}

    def test_utc_matching_units_and_boundaries(self):
        weather = get_weather_at_eta(self.series, "2026-11-15T07:20:00-05:00")
        self.assertEqual(weather["forecast_time"], "2026-11-15T13:00:00+00:00")
        self.assertAlmostEqual(weather["snow_in_per_hr"], 1)
        self.assertAlmostEqual(weather["rain_in_per_hr"], .15)
        for stamp in ["2026-11-15T11:00:00+00:00", "2026-11-18T00:00:00+00:00", "2026-11-15T12:00:00"]:
            with self.assertRaises(ValueError): get_weather_at_eta(self.series, stamp)

    def test_missing_hour_is_not_substituted(self):
        self.series["hourly"]["time"][1] = "2026-11-15T14:00"
        with self.assertRaises(ValueError):
            get_weather_at_eta(self.series, "2026-11-15T13:00:00+00:00")

    @patch("routing.analysis.get_hourly_weather_many")
    def test_actual_hourly_risks_and_missing_coverage(self, fetch):
        fetch.return_value = [self.series, self.series]
        route = {"summary": {"length": 20, "time": 3600}, "legs": [{"shape": polyline.encode([(41,-87),(42,-86)],precision=6)}]}
        result = analyze_route_weather(route,"2026-11-15T12:20:00+00:00",42000)
        self.assertEqual(len(result["forecast_times"]),49)
        self.assertEqual(result["forecast_times"][0],"2026-11-15T13:00:00+00:00")
        cp=result["checkpoints"][0]
        self.assertEqual(cp["hourly_forecast"][0]["risk"]["overall_risk"],"High")
        self.assertEqual(cp["hourly_forecast"][24]["risk"]["overall_risk"],"No Travel")
        self.assertEqual(fetch.call_count,1)
        self.assertEqual(rank_routes([{**result,"route_id":1}])["recommended_route"]["route_id"],1)
        self.series["hourly"]["wind_speed_10m"][-1]=None
        result=analyze_route_weather(route,"2026-11-15T12:20:00+00:00",42000)
        self.assertIsNone(result["checkpoints"][0]["hourly_forecast"][48])

    @patch("routing.http.requests.request")
    def test_weather_cache(self, get):
        cache.clear()
        get.return_value.json.return_value=self.series
        self.assertEqual(get_hourly_weather(41,-87),get_hourly_weather(41,-87))
        self.assertEqual(get.call_count,1)

    @patch("routing.http.requests.request")
    def test_weather_batches_multiple_coordinates(self, get):
        cache.clear()
        get.return_value.json.return_value = [self.series, self.series]
        results = get_hourly_weather_many([(41, -87), (42, -86)])
        self.assertEqual(len(results), 2)
        self.assertEqual(get.call_count, 1)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["latitude"], "41,42")
        self.assertEqual(params["longitude"], "-87,-86")


class LocationSearchTests(SimpleTestCase):
    @patch("routing.http.requests.request")
    def test_search_formats_and_caches_locations(self, get):
        cache.clear()
        response = Mock()
        response.json.return_value = {"results": [{
            "name": "Lahore",
            "admin1": "Punjab",
            "country": "Pakistan",
            "latitude": 31.56,
            "longitude": 74.35,
        }]}
        get.return_value = response

        expected = [{
            "label": "Lahore, Punjab, Pakistan",
            "latitude": 31.56,
            "longitude": 74.35,
        }]
        self.assertEqual(search_locations("Lahore"), expected)
        self.assertEqual(search_locations("Lahore"), expected)
        self.assertEqual(get.call_count, 1)

    @patch("routing.views.search_locations")
    def test_location_search_endpoint(self, search):
        search.return_value = [{"label": "Pakistan"}]
        response = self.client.get("/api/locations/?q=Pakistan")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"label": "Pakistan"}])
        self.assertEqual(self.client.get("/api/locations/?q=x").json(), [])

    @patch("routing.views.geocode_location")
    def test_selected_coordinates_skip_second_geocoder(self, geocode):
        trip = {
            "origin": "Chicago, Illinois, USA",
            "origin_lat": 41.8781,
            "origin_lon": -87.6298,
        }
        self.assertEqual(
            trip_location(trip, "origin"),
            {"lat": 41.8781, "lon": -87.6298},
        )
        geocode.assert_not_called()

    def test_coordinates_must_be_complete(self):
        serializer = TripSerializer(data={
            "origin": "Chicago",
            "origin_lat": 41.8781,
            "destination": "Detroit",
            "departure_time": "2026-11-15T12:00:00Z",
            "load_weight": 42000,
            "checkpoint_interval": 25,
        })
        self.assertFalse(serializer.is_valid())

    @patch("routing.services.request")
    def test_routing_coverage_uses_located_edges_and_cache(self, send):
        cache.clear()
        send.return_value.json.return_value = [{"edges": [{"way_id": 1}]}]
        self.assertTrue(location_is_covered(41.8781, -87.6298))
        self.assertTrue(location_is_covered(41.8781, -87.6298))
        self.assertEqual(send.call_count, 1)

    @patch("routing.views.location_is_covered", return_value=False)
    def test_coverage_endpoint_reports_unsupported_location(self, covered):
        response = self.client.get("/api/coverage/?lat=31.558&lon=74.35071")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"covered": False})
        covered.assert_called_once_with(31.558, 74.35071)
        self.assertEqual(
            self.client.get("/api/coverage/?lat=invalid&lon=74").status_code,
            400,
        )


class HttpRetryTests(SimpleTestCase):
    @patch("routing.http.time.sleep")
    @patch("routing.http.requests.request")
    def test_retries_transient_connection_failure(self, send, sleep):
        response = Mock(status_code=200)
        send.side_effect = [requests.ConnectionError(), response]
        self.assertIs(request("GET", "https://example.test"), response)
        self.assertEqual(send.call_count, 2)
        sleep.assert_called_once()

    @patch("routing.http.time.sleep")
    @patch("routing.http.requests.request")
    def test_does_not_retry_permanent_failure(self, send, sleep):
        response = Mock(status_code=400)
        send.return_value = response
        self.assertIs(request("GET", "https://example.test"), response)
        self.assertEqual(send.call_count, 1)
        sleep.assert_not_called()

    @patch("routing.http.time.sleep")
    @patch("routing.http.requests.request")
    def test_can_disable_retries_for_interactive_search(self, send, sleep):
        send.side_effect = requests.ConnectionError()
        with self.assertRaises(requests.ConnectionError):
            request("GET", "https://example.test", retries=0)
        self.assertEqual(send.call_count, 1)
        sleep.assert_not_called()
