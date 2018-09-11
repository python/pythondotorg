from django import forms

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail

from django.template import loader


def set_placeholder(value):
    return forms.TextInput(attrs={'placeholder': value, 'required': 'required'})


class EventForm(forms.Form):
    event_name = forms.CharField(widget=set_placeholder(
        'Name of the event (including the user group name for '
        'user group events)'
    ))
    event_type = forms.CharField(widget=set_placeholder(
        'conference, bar camp, sprint, user group meeting, etc.'
    ))
    python_focus = forms.CharField(widget=set_placeholder(
        'Data analytics, Web Development, Country-wide conference, etc...'
    ))
    expected_attendees = forms.CharField(widget=set_placeholder('300+'))
    location = forms.CharField(widget=set_placeholder(
        'IFEMA building, Madrid, Spain'
    ))
    date_from = forms.DateField(widget=forms.SelectDateWidget())
    date_to = forms.DateField(widget=forms.SelectDateWidget())
    recurrence = forms.CharField(widget=set_placeholder(
        'None, every second Thursday, monthly, etc.'
    ))
    link = forms.URLField(label='Website URL')
    description = forms.CharField(widget=forms.Textarea)

    def send_email(self, creator):
        context = {
            'event': self.cleaned_data,
            'creator': creator,
            'site': Site.objects.get_current(),
        }
        text_message_template = loader.get_template('events/email/new_event.txt')
        text_message = text_message_template.render(context)
        send_mail(
            subject='New event submission: "{}"'.format(self.cleaned_data['event_name']),
            message=text_message,
            from_email=creator.email,
            recipient_list=[settings.EVENTS_TO_EMAIL],
        )
