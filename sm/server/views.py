from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Server
from . forms import Form
from . forms import FormDisabled

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy

from django.contrib import messages


class ServerListView(LoginRequiredMixin, ListView):
    template_name = 'server/list.html'
    model = Server
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'hostname'


class ServerDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'server/detail.html'
    model = Server
    form_class = FormDisabled


class ServerUpdateView(ServerDetailView, SuccessMessageMixin):
    template_name = 'server/edit.html'
    form_class = Form
    success_url = reverse_lazy('server:index')
    success_message = "%(hostname)s " + _('was updated successfully')


class ServerCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'server/edit.html'
    form_class = Form
    model = Server
    success_url = reverse_lazy('server:index')
    success_message = "%(hostname)s " + _('was created successfully')


class ServerDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'server/delete.html'
    model = Server
    success_url = reverse_lazy('server:index')
    success_message = "%(hostname)s " + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(ServerDeleteView, self).delete(request, *args, **kwargs)


class ServerSearchView(LoginRequiredMixin, ListView):
    template_name = 'server/list.html'
    model = Server
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'hostname'
