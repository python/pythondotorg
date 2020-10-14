from django import forms

from minutes.meetings_factories import new_psf_board_meeting


class NewPSFBoardMeetingForm(forms.Form):
    date = forms.DateField()

    def save(self):
        return new_psf_board_meeting(self.cleaned_data["date"])
