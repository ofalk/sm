from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from .views import DashboardView, SearchView
from .views_avatars import avatar_proxy

import debug_toolbar

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    
    # Allauth URLs
    path('accounts/', include('allauth.urls')),

    # Dashboard & Search
    path('', DashboardView.as_view(), name='dashboard'),
    path('search/', SearchView.as_view(), name='search'),
    path('avatar/<str:email_hash>/', avatar_proxy, name='avatar_proxy'),

    # Project Apps
    path('cluster/', include('cluster.urls')),
    path('operatingsystem/', include('operatingsystem.urls')),
    path('clusterpackage/', include('clusterpackage.urls')),
    path('patchtime/', include('patchtime.urls')),
    path('location/', include('location.urls')),
    path('servermodel/', include('servermodel.urls')),
    path('server/', include('server.urls')),
    path('status/', include('status.urls')),
    path('domain/', include('domain.urls')),
    path('clustersoftware/', include('clustersoftware.urls')),
    path('clusterpackagetype/', include('clusterpackagetype.urls')),
    path('vendor/', include('vendor.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
