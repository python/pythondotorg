import factory

from .models import StoryCategory, Story


class StoryCategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = StoryCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Story Category {}'.format(n))


class StoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = Story

    category = factory.SubFactory(StoryCategoryFactory)
    name = factory.Sequence(lambda n: 'Success Story #{}'.format(n))
    company_name = factory.Faker('company')
    company_url = 'http://www.example.com/'
    author = factory.Faker('name')
    author_email = factory.LazyAttribute(lambda a: '{}@example.com'.format(a.author.replace(' ', '-')).lower())
    pull_quote = factory.Faker('sentence', nb_words=10)
    content = factory.Faker('paragraph', nb_sentences=5)
    is_published = True
