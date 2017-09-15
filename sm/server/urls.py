from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views
from . import app_label as app_name

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

urlpatterns = [
    url(r'^$'.format(extra), views.ListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.CreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.DetailView.as_view(), name='detail'),
    url(r'^update/(?P<pk>[-\w]+)/$'.format(extra),
        views.UpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>[-\w]+)/$'.format(extra),
        views.DeleteView.as_view(), name='delete'),
    url(r'^search$'.format(extra),
        views.SearchView.as_view(), name='search'),
]
