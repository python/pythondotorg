"""Custom managers and querysets for the User model."""

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):
    """QuerySet with convenience filters for active users."""

    def active(self):
        """Filter to active users only."""
        return self.filter(is_active=True)


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    """Custom user manager with UserQuerySet methods available on the manager."""

    # 'UserManager.use_in_migrations' is set to True in Django 1.8:
    # https://github.com/django/django/blob/1.8.18/django/contrib/auth/models.py#L166
    use_in_migrations = False
