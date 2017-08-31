from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Operatingsystem

from django.views.generic.edit import UpdateView, CreateView


class OperatingsystemListView(LoginRequiredMixin, ListView):
    template_name = 'operatingsystem/list.html'
    model = Operatingsystem
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = ['vendor', 'version']


class OperatingsystemDetailView(UpdateView):
    template_name = 'operatingsystem/detail.html'
    fields = '__all__'
    model = Operatingsystem


class OperatingsystemCreateView(CreateView):
    template_name = 'operatingsystem/detail.html'
    fields = '__all__'
    model = Operatingsystem
