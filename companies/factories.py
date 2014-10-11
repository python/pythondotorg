import factory

from .models import Company

__all__ = (
    'CompanyFactory'
)


class CompanyFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Company
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Company {}'.format(n))
    email = factory.Sequence(lambda n: 'zombie_{}@python.org'.format(n))
