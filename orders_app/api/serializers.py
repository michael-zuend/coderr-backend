from rest_framework import serializers

from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """All fields of an order."""

    price = serializers.FloatField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer_user", "business_user", "title", "revisions",
            "delivery_time_in_days", "price", "features", "offer_type",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    """Validates the offer detail id of a new order."""

    offer_detail_id = serializers.IntegerField(min_value=1)


class OrderStatusSerializer(serializers.ModelSerializer):
    """Updates only the status of an order."""

    class Meta:
        model = Order
        fields = ["status"]
        extra_kwargs = {"status": {"required": True}}

    def validate(self, attrs):
        """Reject every field except status."""
        unknown = set(self.initial_data) - {"status"}
        if unknown:
            raise serializers.ValidationError(
                {field: "This field cannot be updated." for field in unknown}
            )
        return attrs
