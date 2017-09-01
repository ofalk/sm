from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Operatingsystem

from django.views.generic.edit import UpdateView, CreateView


class OperatingsystemListView(LoginRequiredMixin, ListView):
    from vendor.models import Vendor
    template_name = 'operatingsystem/list.html'
    model = Vendor
    paginate_by = 20
    queryset = Vendor.objects.all()
    orphans = 3
    ordering = 'name'


class OperatingsystemDetailView(UpdateView):
    template_name = 'operatingsystem/detail.html'
    fields = '__all__'
    model = Operatingsystem


class OperatingsystemCreateView(CreateView):
    template_name = 'operatingsystem/detail.html'
    fields = '__all__'
    model = Operatingsystem

    def get_initial(self):
        from vendor.models import Vendor
        initial = super(OperatingsystemCreateView, self).get_initial()
        if 'vendor' in self.kwargs:
            initial['vendor'] = Vendor.objects.filter(
                name=self.kwargs['vendor']).first()
        return initial
