from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'servermodel'

urlpatterns = [
    url(r'^$'.format(extra), views.ServermodelListView.as_view(),
        name='index'),
    url(r'^create$'.format(extra),
        views.ServermodelCreateView.as_view(), name='create'),
    url(r'^create/(?P<vendor>[\w\s]+)$'.format(extra),
        views.ServermodelCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.ServermodelDetailView.as_view(), name='detail'),
]
