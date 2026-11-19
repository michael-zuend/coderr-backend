from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from profile_app.models import Profile


def create_user(username, profile_type, password="testpass123"):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(
        username=username, email=f"{username}@mail.de", password=password
    )
    Profile.objects.create(user=user, type=profile_type)
    return user


def authenticate(client, user):
    """Authenticate the test client with the token of the user."""
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
