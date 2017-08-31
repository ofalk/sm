from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Domain

from django.views.generic.edit import UpdateView, CreateView


class DomainListView(LoginRequiredMixin, ListView):
    template_name = 'domain/list.html'
    model = Domain
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class DomainDetailView(UpdateView):
    template_name = 'domain/detail.html'
    fields = '__all__'
    model = Domain


class DomainCreateView(CreateView):
    template_name = 'domain/detail.html'
    fields = '__all__'
    model = Domain
