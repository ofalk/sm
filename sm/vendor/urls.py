from django.conf import settings
from django.conf.urls import url

from social_core.utils import setting_name
from . import views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

app_name = 'vendor'

urlpatterns = [
    url(r'^$'.format(extra), views.VendorListView.as_view(), name='index'),
    url(r'^create$'.format(extra),
        views.VendorCreateView.as_view(), name='create'),
    url(r'^detail/(?P<pk>[-\w]+)/$'.format(extra),
        views.VendorDetailView.as_view(), name='detail'),
]
