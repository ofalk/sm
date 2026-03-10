from django.urls import re_path as url

from . import views

app_name = "clustersoftware"


urlpatterns = [
    url(r"^$", views.ListView.as_view(), name="index"),
    url(r"^create$", views.CreateView.as_view(), name="create"),
    url(r"^create/(?P<vendor>[\w\s]+)$", views.CreateView.as_view(), name="create"),
    url(r"^detail/(?P<pk>[-\w]+)/$", views.DetailView.as_view(), name="detail"),
    url(r"^update/(?P<pk>[-\w]+)/$", views.UpdateView.as_view(), name="update"),
    url(r"^delete/(?P<pk>[-\w]+)/$", views.DeleteView.as_view(), name="delete"),
]
