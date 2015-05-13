import factory

from .models import Company

__all__ = (
    'CompanyFactory'
)


class CompanyFactory(factory.DjangoModelFactory):

    class Meta:
        model = Company
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Company {}'.format(n))
    email = factory.Sequence(lambda n: 'zombie_{}@python.org'.format(n))
