from django import forms


class EventForm(forms.Form):
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)

