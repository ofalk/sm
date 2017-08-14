from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'server'

urlpatterns = [
    url(r'^$'.format(extra), views.ServerView.as_view(), name='index'),
]
