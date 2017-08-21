from django.db.models.query import QuerySet
from django.contrib.auth.models import UserManager as DjangoUserManager


class UserQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def searchable(self):
        return self.active().filter(
            public_profile=True,
            search_visibility__exact=self.model.SEARCH_PUBLIC,
        )


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    # 'UserManager.use_in_migrations' is set to True in Django 1.8:
    # https://github.com/django/django/blob/1.8.18/django/contrib/auth/models.py#L166
    use_in_migrations = False
