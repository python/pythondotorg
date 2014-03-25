import factory

from .models import User, Membership


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    FACTORY_DJANGO_GET_OR_CREATE = ('username',)

    username = factory.Sequence(lambda n: 'zombie{0}'.format(n))
    email = factory.Sequence(lambda n: "zombie%s@example.com" % n)
    #password = ?
    search_visibility = User.SEARCH_PUBLIC
    email_privacy = User.EMAIL_PUBLIC


class StaffUserFactory(UserFactory):
    is_staff = True


class MembershipFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Membership
    FACTORY_DJANGO_GET_OR_CREATE = ('creator',)

    psf_code_of_conduct = True
    psf_announcements = True

    creator = factory.SubFactory(UserFactory)
