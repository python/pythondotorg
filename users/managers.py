from django.contrib.auth.models import UserManager as BaseUserManager
from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):

    def public_email(self):
        return self.filter(email_privacy__exact=self.model.SEARCH_PUBLIC)

    def searchable(self):
        return self.filter(
            public_profile=True,
            search_visibility__exact=self.model.SEARCH_PUBLIC,
        )

    def public_profile(self):
        return self.filter(public_profile=True)


class UserManager(BaseUserManager):

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def public_email(self):
        return self.get_queryset().email_is_public()

    def searchable(self):
        return self.get_queryset().searchable()

    def public_profile(self):
        return self.get_queryset().public_profile()
