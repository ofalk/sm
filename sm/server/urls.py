from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'server'

urlpatterns = [
    url(r'^$'.format(extra), views.ServerListView.as_view(), name='index'),
    url(r'^(?P<pk>[-\w]+)/$'.format(extra),
        views.ServerDetailView.as_view(), name='detail'),
]
