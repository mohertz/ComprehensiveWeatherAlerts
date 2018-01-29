from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import ForecastProfile
from . import choices


class NewForecastForm(forms.ModelForm):
    class Meta:
        model = ForecastProfile
        exclude = ['userid', 'last_updated']

    nickname = forms.CharField(label=_('Forecast Nickname'))
    locations = forms.CharField(label=_('Locations (Enter zip codes separated by a space.)'))
    timezone = forms.ChoiceField(label=_('Timezone for your forecast'),choices=choices.timezones)
    start_time = forms.ChoiceField(label=_('Earliest time you want in your forecast (It will not be exact, due to forecast data.)'),choices=choices.times)
    end_time = forms.ChoiceField(label=_('Latest time you want in your forecast (It will not be exact, due to forecast data.)'),choices=choices.times)
    alerts = forms.MultipleChoiceField(choices=choices.alerts, widget=forms.CheckboxSelectMultiple())
    days_in_forecast = forms.ChoiceField(choices=choices.forecastdays)

