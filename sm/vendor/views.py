from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Vendor

from django.views.generic.edit import UpdateView, CreateView


class VendorListView(LoginRequiredMixin, ListView):
    template_name = 'vendor/list.html'
    model = Vendor
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class VendorDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'vendor/detail.html'
    fields = '__all__'
    model = Vendor


class VendorCreateView(LoginRequiredMixin, CreateView):
    template_name = 'vendor/detail.html'
    fields = '__all__'
    model = Vendor
