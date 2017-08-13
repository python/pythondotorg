import factory

from users.factories import UserFactory

from .models import Page


class PageFactory(factory.DjangoModelFactory):

    class Meta:
        model = Page
        django_get_or_create = ('path',)

    title = factory.Sequence(lambda n: 'Page Title #{}'.format(n))
    path = factory.Sequence(lambda n: '/page-title-{}/'.format(n))
    content = factory.Faker('paragraph', nb_sentences=5)
    creator = factory.SubFactory(UserFactory)
