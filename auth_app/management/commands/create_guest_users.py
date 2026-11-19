from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from profile_app.models import Profile

GUEST_USERS = [
    {"username": "andrey", "password": "asdasd", "type": "customer"},
    {"username": "kevin", "password": "asdasd24", "type": "business"},
]


class Command(BaseCommand):
    """Create the guest accounts used by the frontend guest login."""

    help = "Create the guest customer and business users."

    def handle(self, *args, **options):
        for guest in GUEST_USERS:
            self.create_guest(guest)

    def create_guest(self, guest):
        """Create one guest user with profile if it does not exist."""
        user, created = User.objects.get_or_create(
            username=guest["username"],
            defaults={"email": f"{guest['username']}@guest.coderr"},
        )
        if created:
            user.set_password(guest["password"])
            user.save()
        Profile.objects.get_or_create(
            user=user, defaults={"type": guest["type"]}
        )
        self.stdout.write(f"Guest user '{user.username}' is ready.")
