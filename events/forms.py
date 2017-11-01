from django import forms


class EventForm(forms.Form):
    event_name = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Name of the event (including the user group name for user group events)'
    }))
    event_type = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'conference, bar camp, sprint, user group meeting, etc.'
    }))
    python_focus = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Data analytics, Web Development, Country-wide conference, etc...'
    }))
    expected_attendees = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '300+'
    }))
    location = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'IFEMA building, Madrid, Spain'
    }))
    date_from = forms.DateField(widget=forms.SelectDateWidget())
    date_to = forms.DateField(widget=forms.SelectDateWidget())
    recurrence = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'None, every second Thursday, monthly, etc.'
    }))
    link = forms.URLField()
    description = forms.CharField(widget=forms.Textarea)


