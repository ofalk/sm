from django.urls import re_path as url

from . import views

app_name = "server"

urlpatterns = [
    url(r"^$", views.ListView.as_view(), name="index"),
    url(r"^create$", views.CreateView.as_view(), name="create"),
    url(r"^detail/(?P<pk>[-\w]+)/$", views.DetailView.as_view(), name="detail"),
    url(r"^update/(?P<pk>[-\w]+)/$", views.UpdateView.as_view(), name="update"),
    url(r"^delete/(?P<pk>[-\w]+)/$", views.DeleteView.as_view(), name="delete"),
    url(
        r"^decommission/(?P<pk>[-\w]+)/$",
        views.DecommissionView.as_view(),
        name="decommission",
    ),
    url(
        r"^restore/(?P<pk>[-\w]+)/$",
        views.RestoreView.as_view(),
        name="restore",
    ),
    url(r"^search$", views.SearchView.as_view(), name="search"),
    url(r"^bulk-action$", views.BulkActionView.as_view(), name="bulk_action"),
    url(r"^export$", views.CSVExportView.as_view(), name="export"),
]
