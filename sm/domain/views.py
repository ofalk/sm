from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Domain
from . forms import DomainForm, DomainFormDisabled

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy

from django.contrib import messages


class DomainListView(LoginRequiredMixin, ListView):
    template_name = 'domain/list.html'
    model = Domain
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class DomainDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'domain/detail.html'
    model = Domain
    form_class = DomainFormDisabled


class DomainUpdateView(DomainDetailView, SuccessMessageMixin):
    template_name = 'domain/edit.html'
    form_class = DomainForm
    success_url = reverse_lazy('domain:index')
    success_message = "%(name)s" + _('was updated successfully')


class DomainCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'domain/edit.html'
    fields = '__all__'
    model = Domain
    success_url = reverse_lazy('domain:index')
    success_message = "%(name)s " + _('was created successfully')


class DomainDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'domain/delete.html'
    model = Domain
    success_url = reverse_lazy('domain:index')
    success_message = "%(name)s " + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(DomainDeleteView, self).delete(request, *args, **kwargs)
