from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Extends the Django user with business or customer profile data."""

    TYPE_CHOICES = [
        ("business", "Business"),
        ("customer", "Customer"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to="profile_pictures/", blank=True)
    location = models.CharField(max_length=100, blank=True, default="")
    tel = models.CharField(max_length=30, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.type})"
