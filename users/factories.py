import factory

from .models import User, Membership


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('user_name')
    email = factory.Faker('free_email')
    password = factory.PostGenerationMethodCall('set_password', 'password')
    search_visibility = factory.Iterator([
        User.SEARCH_PUBLIC,
        User.SEARCH_PRIVATE,
    ])
    email_privacy = factory.Iterator([
        User.EMAIL_PUBLIC,
        User.EMAIL_PRIVATE,
        User.EMAIL_NEVER,
    ])
    membership = factory.RelatedFactory('users.factories.MembershipFactory', 'creator')

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)


class MembershipFactory(factory.DjangoModelFactory):

    class Meta:
        model = Membership
        django_get_or_create = ('creator',)

    psf_code_of_conduct = True
    psf_announcements = True

    creator = factory.SubFactory(UserFactory, membership=None)


def initial_data():
    return {
        'users': UserFactory.create_batch(size=10),
    }
