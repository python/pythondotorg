from django import forms

from pytz import common_timezones, timezone

from .models import OccurringTime, RecurringTime


class EventTimeForm(forms.ModelForm):
    TZ_CHOICES = ((tz_name, tz_name) for tz_name in common_timezones)

    timezone = forms.CharField(choices=TZ_CHOICES)

    def clean_dt_start(self):
        cleaned_data = self.cleaned_data
        tz = timezone(cleaned_data['timezone'])
        cleaned_data['dt_start'] = cleaned_data['dt_start'].replace(tzinfo=tz)
        cleaned_data['dt_end'] = cleaned_data['dt_end'].replace(tzinfo=tz)

        del cleaned_data['timezone']

        return cleaned_data


class OccurringTimeForm(EventTimeForm):
    class Meta:
        model = OccurringTime


class RecurringTimeForm(EventTimeForm):
    class Meta:
        model = RecurringTime
