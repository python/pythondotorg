from django import forms


class EventForm(forms.Form):
    event_name = forms.CharField()
    event_type = forms.CharField()
    python_focus = forms.CharField()
    expected_attendees = forms.CharField()
    location = forms.CharField()
    date_from = forms.CharField()
    date_to = forms.CharField()
    link = forms.URLField()
    notes = forms.CharField(widget=forms.Textarea)


