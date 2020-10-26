from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from minutes.meetings_factories import new_psf_board_meeting


class NewPSFBoardMeetingForm(forms.Form):
    date = forms.DateField(widget=AdminDateWidget())

    def save(self):
        return new_psf_board_meeting(self.cleaned_data["date"])
