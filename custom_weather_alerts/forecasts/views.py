from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.urls import reverse_lazy
from django.core import validators
from django.views import View
from django.views.generic import DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, FormView
from django.views.generic.edit import SingleObjectMixin
from django.http import HttpResponseRedirect
from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _


from django.contrib.auth.mixins import LoginRequiredMixin

from .models import ForecastProfile
from .forms import *


class UserForecasts(LoginRequiredMixin, ListView):
    model = ForecastProfile
    template_name = 'users/user_forecasts.html'

    def get_queryset(self):
        return ForecastProfile.objects.filter(userid_id=self.request.user)


class NewForecast(LoginRequiredMixin, CreateView):
    model = ForecastProfile
    form_class = NewForecastForm
    template_name = 'users/new_forecast.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial={'nickname':(request.user.username + str(ForecastProfile.objects.filter(userid_id=self.request.user).count() + 1)), 'timezone': request.user.dtz, 'days_in_forecast': request.user.dday, 'start_time': 0, 'end_time': 23})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            f=form.save(commit=False)
            f.userid = request.user
            f.save()

            return redirect('forecasts:list')

        return render(request, self.template_name, {'form': form})


class ForecastDelete(LoginRequiredMixin, DeleteView):
    model = ForecastProfile
    success_url = reverse_lazy('forecasts:list')

    def get(self, request, *args, **kwargs):
        forecast = get_object_or_404(ForecastProfile, pk=pk)

        if request.method == 'POST':
            forecast.delete()
            return redirect('forecasts:list')


class SendForecastNow(LoginRequiredMixin, DetailView):
    model = ForecastProfile
    def get(self, request, *args, **kwargs):
        forecast = self.get_object()

        if request.method == 'GET':
            forecast.CheckForecast()
            return redirect('forecasts:list')
