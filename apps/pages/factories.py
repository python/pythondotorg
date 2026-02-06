"""Factory Boy factories for generating test Page instances."""

import factory
from django.template.defaultfilters import slugify
from factory.django import DjangoModelFactory

from apps.pages.models import Page
from apps.users.factories import UserFactory


class PageFactory(DjangoModelFactory):
    """Factory for creating Page instances in tests."""

    class Meta:
        """Meta configuration for PageFactory."""

        model = Page
        django_get_or_create = ("path",)

    title = factory.Faker("sentence", nb_words=5)
    path = factory.LazyAttribute(lambda o: slugify(o.title))
    content = factory.Faker("paragraph", nb_sentences=5)
    creator = factory.SubFactory(UserFactory)


def initial_data():
    """Generate a batch of 50 sample Page instances for development seeding."""
    return {
        "pages": PageFactory.create_batch(size=50),
    }
