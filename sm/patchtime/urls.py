from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'patchtime'

urlpatterns = [
    url(r'^$'.format(extra), views.PatchtimeListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.PatchtimeCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.PatchtimeDetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$'.format(extra),
        views.PatchtimeUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$'.format(extra),
        views.PatchtimeDeleteView.as_view(), name='delete'),
]
