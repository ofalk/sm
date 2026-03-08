from django.conf import settings
from django.urls import re_path as url

from social_core.utils import setting_name
from . import views
from . import app_label as app_name



urlpatterns = [
    url(r'^$', views.ListView.as_view(), name='index'),
    url(r'^create$',
        views.CreateView.as_view(), name='create'),
    url(r'^create/(?P<vendor>[\w\s]+)$',
        views.CreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$',
        views.DetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$',
        views.UpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$',
        views.DeleteView.as_view(), name='delete'),
]
