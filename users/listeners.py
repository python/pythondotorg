"""Signal listeners for creating API tokens on user creation."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from users.models import User


@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    """Create a DRF auth token automatically when a new user is created."""
    if created:
        Token.objects.create(user=instance)
