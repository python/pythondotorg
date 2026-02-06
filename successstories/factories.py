"""Factory Boy factories for generating test success story instances."""

import factory
from factory.django import DjangoModelFactory
from faker.providers import BaseProvider

from successstories.models import Story, StoryCategory


class StoryProvider(BaseProvider):
    """Faker provider supplying random story category names."""

    story_categories = [
        "Arts",
        "Business",
        "Education",
        "Engineering",
        "Government",
        "Scientific",
        "Software Development",
    ]

    def story_category(self):
        """Return a random story category name."""
        return self.random_element(self.story_categories)


factory.Faker.add_provider(StoryProvider)


class StoryCategoryFactory(DjangoModelFactory):
    """Factory for creating StoryCategory instances in tests."""

    class Meta:
        """Meta configuration for StoryCategoryFactory."""

        model = StoryCategory
        django_get_or_create = ("name",)

    name = factory.Faker("story_category")


class StoryFactory(DjangoModelFactory):
    """Factory for creating Story instances in tests."""

    class Meta:
        """Meta configuration for StoryFactory."""

        model = Story
        django_get_or_create = ("name",)

    category = factory.SubFactory(StoryCategoryFactory)
    name = factory.LazyAttribute(lambda o: f"Success Story of {o.company_name}")
    company_name = factory.Faker("company")
    company_url = factory.Faker("url")
    author = factory.Faker("name")
    author_email = factory.Faker("email")
    pull_quote = factory.Faker("sentence", nb_words=10)
    content = factory.Faker("paragraph", nb_sentences=5)
    is_published = True


def initial_data():
    """Generate sample success stories including one featured story for development seeding."""
    return {
        "successstories": [*StoryFactory.create_batch(size=10), StoryFactory(featured=True)],
    }
