import datetime
from unittest.mock import patch

from django.test import TestCase

from ..forms import NewPSFBoardMeetingForm


class NewPSFBoardMeetingFormTests(TestCase):

    def test_required_fields(self):
        required_fields = ["date"]

        form = NewPSFBoardMeetingForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), len(required_fields))
        for field in required_fields:
            self.assertIn(field, form.errors)

    @patch("minutes.forms.new_psf_board_meeting")
    def test_create_new_psf_meeting_if_valid(self, mocked_new_psf_board_meeting):
        date = datetime.date.today()

        form = NewPSFBoardMeetingForm(data={"date": date})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.save(), mocked_new_psf_board_meeting.return_value)
        mocked_new_psf_board_meeting.assert_called_once_with(date)
