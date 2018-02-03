from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

from .models import ForecastProfile
from . import choices


class ThreeNumFields(forms.MultiWidget):
    def __init__(self, attrs=None):
        self.widgets = [
            forms.TextInput(),
            forms.TextInput(),
            forms.TextInput()
        ]
        super().__init__(self.widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split(' ')
        return [None, None]


class LocationMultiField(forms.MultiValueField):
    widget = ThreeNumFields()
    validators = [RegexValidator]

    def __init__(self):
        fields = (
            forms.CharField(
                error_messages={'incomplete': 'Please enter at least one valid zip code.'},
                validators=[
                    RegexValidator(r'^[0-9]+$', 'Enter a valid US zip code.'),
                ],
                max_length=5,
            ),
            forms.CharField(
                required=False,
                validators=[
                    RegexValidator(r'^[0-9]+$', 'Enter a valid US zip code.'),
                ],
                max_length=5,
            ),
            forms.CharField(
                required=False,
                validators=[
                    RegexValidator(r'^[0-9]+$', 'Enter a valid US zip code.'),
                ],
                max_length=5,
            )
        )
        super(LocationMultiField, self).__init__(
            fields=fields,
            require_all_fields=False
        )

    def compress(self, data_list):
        return ' '.join(data_list)


class NewForecastForm(forms.ModelForm):
    class Meta:
        model = ForecastProfile
        exclude = ['userid', 'last_updated']

    nickname = forms.CharField(
        label=_('Forecast Nickname')
    )
    locations = forms.CharField(
        label=_('Location zip code(s)'),
        help_text=_('(If you want multiple locations, separate them by a space.')
    )
    timezone = forms.ChoiceField(
        label=_('Timezone for your forecast'),
        choices=choices.timezones
    )
    start_time = forms.ChoiceField(
        label=_('Earliest time you want in your forecast'),
        help_text=_('(Time will not be exact to account for timezone conversions and forecast data.)'),
        choices=choices.times
    )
    end_time = forms.ChoiceField(
        label=_('Latest time you want in your forecast'),
        help_text=_('(Time will not be exact to account for timezone conversions and forecast data.)'),
        choices=choices.times
    )
    alerts = forms.MultipleChoiceField(
        choices=choices.alerts,
        widget=forms.CheckboxSelectMultiple()
    )
    days_in_forecast = forms.ChoiceField(
        choices=choices.forecastdays
    )

