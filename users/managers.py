from django.db.models import Manager
from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):

    def public_email(self):
        return self.filter(email_privacy__exact=self.model.SEARCH_PUBLIC)

    def receive_psf_announcements(self):
        return self.filter(psf_announcements__exact=True)

    def searchable(self):
        return self.filter(search_visibility__exact=self.model.SEARCH_PUBLIC)


class UserManager(Manager):

    def get_query_set(self):
        return UserQuerySet(self.model, using=self._db)

    def public_email(self):
        return self.get_query_set().email_is_public()

    def receive_psf_announcements(self):
        return self.get_query_set().receive_psf_announcements()

    def searchable(self):
        return self.get_query_set().searchable()
