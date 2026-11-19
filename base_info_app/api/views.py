from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profile_app.models import Profile
from reviews_app.models import Review


class BaseInfoView(APIView):
    """Return general statistics about the platform."""

    permission_classes = [AllowAny]

    def get(self, request):
        average = Review.objects.aggregate(avg=Avg("rating"))["avg"] or 0
        return Response({
            "review_count": Review.objects.count(),
            "average_rating": round(average, 1),
            "business_profile_count": Profile.objects.filter(
                type="business"
            ).count(),
            "offer_count": Offer.objects.count(),
        })
