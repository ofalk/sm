from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Patchtime
from . forms import PatchtimeForm, PatchtimeFormDisabled

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy

from django.contrib import messages


class PatchtimeListView(LoginRequiredMixin, ListView):
    template_name = 'patchtime/list.html'
    model = Patchtime
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class PatchtimeDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'patchtime/detail.html'
    model = Patchtime
    form_class = PatchtimeFormDisabled


class PatchtimeUpdateView(PatchtimeDetailView, SuccessMessageMixin):
    template_name = 'patchtime/edit.html'
    form_class = PatchtimeForm
    success_url = reverse_lazy('patchtime:index')
    success_message = "%(name)s" + _('was updated successfully')


class PatchtimeCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'patchtime/edit.html'
    fields = '__all__'
    model = Patchtime
    success_url = reverse_lazy('patchtime:index')
    success_message = "%(name)s " + _('was created successfully')


class PatchtimeDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'patchtime/delete.html'
    model = Patchtime
    success_url = reverse_lazy('patchtime:index')
    success_message = "%(name)s " + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(PatchtimeDeleteView, self).delete(request, *args, **kwargs)
