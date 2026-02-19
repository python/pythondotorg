"""Factory Boy factories for generating test user and membership data."""

import factory
from factory.django import DjangoModelFactory

from apps.users.models import Membership, User


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances with realistic test data."""

    class Meta:
        """Meta configuration for UserFactory."""

        model = User
        django_get_or_create = ("username",)

    username = factory.Faker("user_name")
    email = factory.Faker("free_email")
    password = factory.PostGenerationMethodCall("set_password", "password")
    search_visibility = factory.Iterator(
        [
            User.SEARCH_PUBLIC,
            User.SEARCH_PRIVATE,
        ]
    )
    email_privacy = factory.Iterator(
        [
            User.EMAIL_PUBLIC,
            User.EMAIL_PRIVATE,
            User.EMAIL_NEVER,
        ]
    )
    membership = factory.RelatedFactory("apps.users.factories.MembershipFactory", "creator")

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Add the user to the specified groups after creation."""
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)


class MembershipFactory(DjangoModelFactory):
    """Factory for creating Membership instances linked to users."""

    class Meta:
        """Meta configuration for MembershipFactory."""

        model = Membership
        django_get_or_create = ("creator",)

    psf_code_of_conduct = True
    psf_announcements = True

    creator = factory.SubFactory(UserFactory, membership=None)


def initial_data():
    """Create a batch of test users with associated memberships."""
    return {
        "users": UserFactory.create_batch(size=10),
    }
