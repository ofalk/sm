from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Servermodel

from django.views.generic.edit import UpdateView, CreateView


class ServermodelListView(LoginRequiredMixin, ListView):
    template_name = 'servermodel/list.html'
    paginate_by = 20
    orphans = 3

    def get_queryset(self):
        from vendor.models import Vendor
        if 'srvmanager-show_empty' in self.request.COOKIES:
            if self.request.COOKIES['srvmanager-show_empty'] == 'false':
                return Vendor.objects.exclude(
                    Servermodel=None).order_by('name')
        return Vendor.objects.all().order_by('name')


class ServermodelDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'servermodel/detail.html'
    fields = '__all__'
    model = Servermodel


class ServermodelCreateView(LoginRequiredMixin, CreateView):
    template_name = 'servermodel/detail.html'
    fields = '__all__'
    model = Servermodel

    def get_initial(self):
        from vendor.models import Vendor
        initial = super(ServermodelCreateView, self).get_initial()
        if 'vendor' in self.kwargs:
            initial['vendor'] = Vendor.objects.filter(
                name=self.kwargs['vendor']).first()
        return initial
