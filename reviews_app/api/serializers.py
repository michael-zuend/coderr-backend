from rest_framework import serializers

from reviews_app.models import Review

REVIEW_FIELDS = [
    "id", "business_user", "reviewer", "rating", "description",
    "created_at", "updated_at",
]


class ReviewSerializer(serializers.ModelSerializer):
    """Creates a review for a business user and shows all its fields."""

    class Meta:
        model = Review
        fields = REVIEW_FIELDS
        read_only_fields = ["reviewer", "created_at", "updated_at"]
        validators = []

    def validate_business_user(self, value):
        """Ensure that the reviewed user is a business user."""
        profile = getattr(value, "profile", None)
        if profile is None or profile.type != "business":
            raise serializers.ValidationError("User is not a business user.")
        return value


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Updates only the rating and the description of a review."""

    class Meta:
        model = Review
        fields = REVIEW_FIELDS
        read_only_fields = [
            "business_user", "reviewer", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        """Reject every field except rating and description."""
        unknown = set(self.initial_data) - {"rating", "description"}
        if unknown:
            raise serializers.ValidationError(
                {field: "This field cannot be updated." for field in unknown}
            )
        return attrs
