"""Factory functions for creating company test and seed data."""

import factory
from factory.django import DjangoModelFactory

from .models import Company


class CompanyFactory(DjangoModelFactory):
    """Factory for creating Company instances in tests."""

    class Meta:
        """Meta configuration for CompanyFactory."""

        model = Company
        django_get_or_create = ("name",)

    name = factory.Faker("company")
    contact = factory.Faker("name")
    email = factory.Faker("company_email")
    url = factory.Faker("url")


def initial_data():
    """Create a batch of sample company records."""
    return {
        "companies": CompanyFactory.create_batch(size=10),
    }
