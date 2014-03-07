import factory

from .models import PepType, PepStatus, PepOwner, PepCategory, Pep


class PepTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PepType
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Pep Type {0}'.format(n))
    abbreviation = factory.Sequence(lambda n: 'pt{0}'.format(n))


class PepStatusFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PepStatus
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Pep Status {0}'.format(n))
    abbreviation = factory.Sequence(lambda n: 'ps{0}'.format(n))


class PepOwnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PepOwner
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Pep Owner {0}'.format(n))
    email = factory.Sequence(lambda n: 'owner_{0}@python.org'.format(n))


class PepCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PepCategory
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Pep Category {0}'.format(n))


class PepFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Pep
    FACTORY_DJANGO_GET_OR_CREATE = ('title',)

    title = factory.Sequence(lambda n: 'Pep {0}'.format(n))
    number = factory.Sequence(lambda n: n)
    url = factory.Sequence(lambda n: 'http://peps.org/{0}/'.format(n))
    status = factory.SubFactory(PepStatusFactory)
    type = factory.SubFactory(PepTypeFactory)
    category = factory.SubFactory(PepCategoryFactory)
