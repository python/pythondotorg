import factory

from .models import User, Membership


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: 'zombie{}'.format(n))
    email = factory.Sequence(lambda n: "zombie%s@example.com" % n)
    password = factory.PostGenerationMethodCall('set_password', 'password')
    search_visibility = User.SEARCH_PUBLIC
    email_privacy = User.EMAIL_PUBLIC


class StaffUserFactory(UserFactory):
    is_staff = True


class MembershipFactory(factory.DjangoModelFactory):

    class Meta:
        model = Membership
        django_get_or_create = ('creator',)

    psf_code_of_conduct = True
    psf_announcements = True

    creator = factory.SubFactory(UserFactory)
