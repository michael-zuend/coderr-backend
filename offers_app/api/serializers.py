from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

OFFER_TYPES = {"basic", "standard", "premium"}


class OfferDetailSerializer(serializers.ModelSerializer):
    """All fields of a single offer package."""

    class Meta:
        model = OfferDetail
        fields = [
            "id", "title", "revisions", "delivery_time_in_days", "price",
            "features", "offer_type",
        ]

    def validate_revisions(self, value):
        """Allow -1 for unlimited revisions, otherwise no negatives."""
        if value < -1:
            raise serializers.ValidationError("Must be -1 or greater.")
        return value

    def validate_delivery_time_in_days(self, value):
        """Ensure that the delivery time is at least one day."""
        if value < 1:
            raise serializers.ValidationError("Must be at least 1 day.")
        return value

    def validate_features(self, value):
        """Ensure that features is a list of strings."""
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Must be a list of strings.")
        return value


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Id and relative url of an offer package, used in offer lists."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailAbsoluteLinkSerializer(OfferDetailLinkSerializer):
    """Id and absolute url of an offer package, used in a single offer."""

    def get_url(self, obj):
        path = reverse("offerdetail-detail", kwargs={"pk": obj.id})
        return self.context["request"].build_absolute_uri(path)


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """A single offer with links to its packages and summary values."""

    details = OfferDetailAbsoluteLinkSerializer(many=True, read_only=True)
    min_price = serializers.FloatField(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description", "created_at",
            "updated_at", "details", "min_price", "min_delivery_time",
        ]


class OfferListSerializer(OfferRetrieveSerializer):
    """An offer in the paginated list, including creator details."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta(OfferRetrieveSerializer.Meta):
        fields = OfferRetrieveSerializer.Meta.fields + ["user_details"]

    def get_user_details(self, obj):
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username,
        }


class OfferWriteSerializer(serializers.ModelSerializer):
    """Creates or updates an offer together with its packages."""

    details = OfferDetailSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        """Check the offer types of the given packages."""
        offer_types = [detail.get("offer_type") for detail in value]
        if None in offer_types:
            raise serializers.ValidationError("Each detail needs offer_type.")
        if len(offer_types) != len(set(offer_types)):
            raise serializers.ValidationError("Offer types must be unique.")
        if self.instance is None and set(offer_types) != OFFER_TYPES:
            raise serializers.ValidationError(
                "An offer needs exactly one basic, standard and premium "
                "detail."
            )
        return value

    def validate(self, attrs):
        """Require the packages when a new offer is created."""
        if self.instance is None and "details" not in attrs:
            raise serializers.ValidationError(
                {"details": "This field is required."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create the offer and its three packages."""
        details = validated_data.pop("details")
        offer = Offer.objects.create(**validated_data)
        for detail in details:
            OfferDetail.objects.create(offer=offer, **detail)
        return offer

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update the offer and the packages matched by offer type."""
        details = validated_data.pop("details", [])
        instance = super().update(instance, validated_data)
        for detail_data in details:
            self.update_detail(instance, detail_data)
        instance.save()
        return instance

    def update_detail(self, offer, detail_data):
        """Update one package of the offer, keeping its id."""
        offer_type = detail_data.get("offer_type")
        detail = offer.details.filter(offer_type=offer_type).first()
        if detail is None:
            raise serializers.ValidationError(
                {"details": f"No detail with offer_type '{offer_type}'."}
            )
        for field, value in detail_data.items():
            setattr(detail, field, value)
        detail.save()
