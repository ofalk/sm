from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'location'

urlpatterns = [
    url(r'^$'.format(extra), views.LocationListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.LocationCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.LocationDetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$'.format(extra),
        views.LocationUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$'.format(extra),
        views.LocationDeleteView.as_view(), name='delete'),
]
