from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def searchable(self):
        return self.active().filter(
            public_profile=True,
            search_visibility__exact=self.model.SEARCH_PUBLIC,
        )
