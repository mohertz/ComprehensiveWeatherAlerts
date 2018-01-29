from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.http import HttpRequest
from allauth.account.models import EmailAddress



@python_2_unicode_compatible
class User(AbstractUser):

    tz_choices = [('US/Alaska','US/Alaska'),('US/Arizona','US/Arizona'),('US/Central','US/Central'),('US/Eastern','US/Eastern'),('US/Hawaii','US/Hawaii'),('US/Mountain','US/Mountain'),('US/Pacific','US/Pacific')]
    fday_choices = [(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')]

    # First Name and Last Name do not cover name patterns around the globe.
    name = models.CharField(_('Name of User'), blank=True, max_length=255)
    dtz = models.CharField(_('Default Timezone'), blank=True, max_length=25, choices=tz_choices)
    dday = models.PositiveSmallIntegerField(_('Default Number of Days in Forecast'), choices=fday_choices, default=5)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})
