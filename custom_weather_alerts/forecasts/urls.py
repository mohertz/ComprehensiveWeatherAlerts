from django.conf.urls import url
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.UserForecasts.as_view(),
        name='list'
    ),
    url(
        regex=r'^~newforecast/$',
        view=views.NewForecast.as_view(),
        name='NewForecast'
    ),
    url(
        regex=r'^delete/(?P<pk>[0-9]+)/$',
        view=views.ForecastDelete.as_view(),
        name='ForecastDelete'
    ),
    url(
        regex=r'^send/(?P<pk>[0-9]+)/$',
        view=views.SendForecastNow.as_view(),
        name='SendForecastNow'
    ),
    url(   # This is not working because I fucked something up
        regex=r'^success/$',
        view=TemplateView.as_view(template_name='success.html'),
        name='success'
    )
]
