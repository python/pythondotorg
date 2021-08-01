import factory
from factory.django import DjangoModelFactory

from .models import Company


class CompanyFactory(DjangoModelFactory):

    class Meta:
        model = Company
        django_get_or_create = ('name',)

    name = factory.Faker('company')
    contact = factory.Faker('name')
    email = factory.Faker('company_email')
    url = factory.Faker('url')


def initial_data():
    return {
        'companies': CompanyFactory.create_batch(size=10),
    }
