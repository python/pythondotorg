from django.db.models.query import QuerySet


class UserQuerySet(QuerySet):

    def searchable(self):
        return self.filter(
            public_profile=True,
            search_visibility__exact=self.model.SEARCH_PUBLIC,
        )
