from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'operatingsystem'

urlpatterns = [
    url(r'^$'.format(extra), views.OperatingsystemListView.as_view(),
        name='index'),
    url(r'^create$'.format(extra),
        views.OperatingsystemCreateView.as_view(), name='create'),
    url(r'^create/(?P<vendor>[\w\s]+)$'.format(extra),
        views.OperatingsystemCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.OperatingsystemDetailView.as_view(), name='detail'),
]
