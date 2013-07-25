import factory

from .models import User


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    FACTORY_DJANGO_GET_OR_CREATE = ('username',)

    username = factory.Sequence(lambda n: 'zombie{0}'.format(n))
    email = factory.Sequence(lambda n: "zombie%s@example.com" % n)
    #password = ?
    psf_code_of_conduct = True
    psf_announcements = True
    search_visibility = User.SEARCH_PUBLIC
    email_privacy = User.EMAIL_PUBLIC
