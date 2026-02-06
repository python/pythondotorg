from django.test import TestCase, RequestFactory

from users.models import User

from nominations.forms import FellowNominationForm
from nominations.models import FellowNominationRound
from nominations.tests.factories import UserFactory, FellowNominationRoundFactory


class FellowNominationFormTests(TestCase):
    def setUp(self):
        self.round = FellowNominationRoundFactory()
        self.user = UserFactory(email="nominator@example.com")
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

    def test_valid_form(self):
        data = {
            "nominee_name": "Jane Doe",
            "nominee_email": "jane@example.com",
            "nomination_statement": "Jane has made outstanding contributions to the Python community through years of dedicated work on documentation, mentoring, and conference organization.",
            "nomination_statement_markup_type": "markdown",
        }
        form = FellowNominationForm(data=data, request=self.request)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = FellowNominationForm(data={}, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertIn("nominee_name", form.errors)
        self.assertIn("nominee_email", form.errors)

    def test_self_nomination_prevented(self):
        data = {
            "nominee_name": "Self Nominator",
            "nominee_email": "nominator@example.com",
            "nomination_statement": "I am great.",
            "nomination_statement_markup_type": "markdown",
        }
        form = FellowNominationForm(data=data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertIn("nominee_email", form.errors)

    def test_self_nomination_case_insensitive(self):
        data = {
            "nominee_name": "Self Nominator",
            "nominee_email": "Nominator@Example.com",
            "nomination_statement": "I am great.",
            "nomination_statement_markup_type": "markdown",
        }
        form = FellowNominationForm(data=data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertIn("nominee_email", form.errors)

    def test_invalid_email(self):
        data = {
            "nominee_name": "Jane Doe",
            "nominee_email": "not-an-email",
            "nomination_statement": "Great contributor.",
            "nomination_statement_markup_type": "markdown",
        }
        form = FellowNominationForm(data=data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertIn("nominee_email", form.errors)
