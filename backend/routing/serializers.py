from rest_framework import serializers

class TripSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure_time = serializers.DateTimeField()
    load_weight = serializers.DecimalField(
        max_digits = 10,
        decimal_places=2,
        min_value=0.01
    )
    checkpoint_interval=serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25
    )