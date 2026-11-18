from django.contrib.auth.models import User
from rest_framework import serializers

from profile_app.models import Profile


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Full profile data including the editable fields of the user."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
            "email", "created_at",
        ]
        read_only_fields = ["user", "type", "created_at"]

    def validate_email(self, value):
        """Ensure that the email is not used by another user."""
        users = User.objects.filter(email__iexact=value)
        if users.exclude(pk=self.instance.user.pk).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def update(self, instance, validated_data):
        """Update the user fields and the profile fields."""
        user_data = validated_data.pop("user", {})
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Profile data shown in the list of business users."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
        ]


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Profile data shown in the list of customers."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    uploaded_at = serializers.DateTimeField(source="created_at")

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "uploaded_at", "type",
        ]
