from django import forms


class EventForm(forms.Form):
    event_name = forms.CharField()
    event_type = forms.CharField()
    python_focus = forms.CharField()
    expected_attendees = forms.CharField()
    location = forms.CharField()
    date_from = forms.DateField(widget=forms.SelectDateWidget())
    date_to = forms.DateField(widget=forms.SelectDateWidget())
    link = forms.URLField()
    description = forms.CharField(widget=forms.Textarea)


