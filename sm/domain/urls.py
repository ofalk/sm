from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views
from . import app_name

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = app_name

urlpatterns = [
    url(r'^$'.format(extra), views.ListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.omainCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.omainDetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$'.format(extra),
        views.omainUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$'.format(extra),
        views.omainDeleteView.as_view(), name='delete'),
]
