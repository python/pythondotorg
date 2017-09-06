import factory

from faker.providers import BaseProvider

from .models import StoryCategory, Story


class StoryProvider(BaseProvider):

    story_categories = [
        'Arts',
        'Business',
        'Education',
        'Engineering',
        'Government',
        'Scientific',
        'Software Development',
    ]

    def story_category(self):
        return self.random_element(self.story_categories)

factory.Faker.add_provider(StoryProvider)


class StoryCategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = StoryCategory
        django_get_or_create = ('name',)

    name = factory.Faker('story_category')


class StoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = Story
        django_get_or_create = ('name',)

    category = factory.SubFactory(StoryCategoryFactory)
    name = factory.LazyAttribute(lambda o: 'Success Story of {}'.format(o.company_name))
    company_name = factory.Faker('company')
    company_url = factory.Faker('url')
    author = factory.Faker('name')
    author_email = factory.Faker('email')
    pull_quote = factory.Faker('sentence', nb_words=10)
    content = factory.Faker('paragraph', nb_sentences=5)
    is_published = True


def initial_data():
    return {
        'successstories': StoryFactory.create_batch(size=10) + [StoryFactory(featured=True)],
    }
