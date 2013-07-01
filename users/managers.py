from django.contrib.auth.models import UserManager as BaseUserManager
from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):

    def public_email(self):
        return self.filter(email_privacy__exact=self.model.SEARCH_PUBLIC)

    def searchable(self):
        return self.filter(search_visibility__exact=self.model.SEARCH_PUBLIC)


class UserManager(BaseUserManager):

    def get_query_set(self):
        return UserQuerySet(self.model, using=self._db)

    def public_email(self):
        return self.get_query_set().email_is_public()

    def searchable(self):
        return self.get_query_set().searchable()
