from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'server'

urlpatterns = [
    url(r'^$'.format(extra), views.ServerListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.ServerCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.ServerDetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$'.format(extra),
        views.ServerUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$'.format(extra),
        views.ServerDeleteView.as_view(), name='delete'),
    url(r'^search$'.format(extra),
        views.ServerSearchView.as_view(), name='search'),
]
