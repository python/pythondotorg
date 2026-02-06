import datetime

import factory
from factory.django import DjangoModelFactory

from nominations.models import FellowNomination, FellowNominationRound
from users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class FellowNominationRoundFactory(DjangoModelFactory):
    class Meta:
        model = FellowNominationRound

    year = 2026
    quarter = 1
    quarter_start = datetime.date(2026, 1, 1)
    quarter_end = datetime.date(2026, 3, 31)
    nominations_cutoff = datetime.date(2026, 2, 20)
    review_start = datetime.date(2026, 2, 20)
    review_end = datetime.date(2026, 3, 20)
    is_open = True


class FellowNominationFactory(DjangoModelFactory):
    class Meta:
        model = FellowNomination

    nominee_name = factory.Faker("name")
    nominee_email = factory.Faker("email")
    nomination_statement = "This person has made great contributions to Python."
    nominator = factory.SubFactory(UserFactory)
    nomination_round = factory.SubFactory(FellowNominationRoundFactory)
    status = "pending"
