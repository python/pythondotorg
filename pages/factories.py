import factory

from django.template.defaultfilters import slugify

from users.factories import UserFactory

from .models import Page


class PageFactory(factory.DjangoModelFactory):

    class Meta:
        model = Page
        django_get_or_create = ('path',)

    title = factory.Faker('sentence', nb_words=5)
    path = factory.LazyAttribute(lambda o: slugify(o.title))
    content = factory.Faker('paragraph', nb_sentences=5)
    creator = factory.SubFactory(UserFactory)


def initial_data():
    return {
        'pages': PageFactory.create_batch(size=50),
    }
