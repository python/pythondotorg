import datetime

from django.test import SimpleTestCase

from ..forms import EventForm


class EventFormTests(SimpleTestCase):

    def test_valid_form(self):
        data = {
            'event_name': 'PyConES17',
            'event_type': 'conference',
            'python_focus': 'Country-wide conference',
            'expected_attendees': '500',
            'location': 'Complejo San Francisco, Caceres, Spain',
            'date_from': datetime.datetime(2017, 9, 22),
            'date_to': datetime.datetime(2017, 9, 25),
            'recurrence': 'None',
            'link': 'https://2017.es.pycon.org/en/',
            'description': 'A conference no one can afford to miss',
        }
        form = EventForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.errors, {})

    def test_invalid_form(self):
        data = {
            'event_name': 'PyConES17',
            'event_type': 'conference',
            'python_focus': 'Country-wide conference',
            'expected_attendees': '500',
            'location': 'Complejo San Francisco, Caceres, Spain',
            'date_to': datetime.datetime(2017, 9, 25),
            'recurrence': 'None',
            'link': 'https://2017.es.pycon.org/en/',
            'description': 'A conference no one can afford to miss',
        }
        form = EventForm(data=data)
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(
            form.errors,
            {'date_from': ['This field is required.']}
        )
