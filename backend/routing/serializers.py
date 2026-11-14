from rest_framework import serializers
from decimal import Decimal


class TripSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    origin_lat = serializers.FloatField(min_value=-90, max_value=90, required=False)
    origin_lon = serializers.FloatField(min_value=-180, max_value=180, required=False)
    destination = serializers.CharField(max_length=200)
    destination_lat = serializers.FloatField(min_value=-90, max_value=90, required=False)
    destination_lon = serializers.FloatField(min_value=-180, max_value=180, required=False)
    departure_time = serializers.DateTimeField()
    load_weight = serializers.DecimalField(
        max_digits = 10,
        decimal_places=2,
        min_value=Decimal("0.01")
    )
    checkpoint_interval=serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25
    )

    def validate(self, attrs):
        for name in ("origin", "destination"):
            has_lat = f"{name}_lat" in attrs
            has_lon = f"{name}_lon" in attrs
            if has_lat != has_lon:
                raise serializers.ValidationError(
                    {name: "Latitude and longitude must be provided together"}
                )
        return attrs
