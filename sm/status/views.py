from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Status
from . forms import StatusForm, StatusFormDisabled

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy

from django.contrib import messages


class StatusListView(LoginRequiredMixin, ListView):
    template_name = 'status/list.html'
    model = Status
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class StatusDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'status/detail.html'
    model = Status
    form_class = StatusFormDisabled


class StatusUpdateView(StatusDetailView, SuccessMessageMixin):
    template_name = 'status/edit.html'
    form_class = StatusForm
    success_url = reverse_lazy('status:index')
    success_message = "%(name)s" + _('was updated successfully')


class StatusCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'status/edit.html'
    fields = '__all__'
    model = Status
    success_url = reverse_lazy('status:index')
    success_message = "%(name)s " + _('was created successfully')


class StatusDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'status/delete.html'
    model = Status
    success_url = reverse_lazy('status:index')
    success_message = "%(name)s " + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(StatusDeleteView, self).delete(request, *args, **kwargs)
