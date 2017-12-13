from __future__ import unicode_literals

from account.mixins import LoginRequiredMixin

from . models import Model
from . forms import Form, FormDisabled
from . import app_label

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

try:
    from django.core.urlresolvers import reverse_lazy
except Exception as e:
    from django.urls import reverse_lazy

from django.contrib import messages


class ListView(LoginRequiredMixin, GenericListView):
    template_name = '%s/list.html' % app_label
    model = Model
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class DetailView(LoginRequiredMixin, GenericUpdateView):
    template_name = '%s/detail.html' % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(DetailView, SuccessMessageMixin):
    template_name = '%s/edit.html' % app_label
    model = Model
    form_class = Form
    success_url = reverse_lazy('%s:index' % app_label)
    success_message = '%(name)s ' + _('was updated successfully')

    def form_valid(self, form):
        self.object.server_set = form.cleaned_data['server_set']
        return super(UpdateView, self).form_valid(form)


class CreateView(SuccessMessageMixin, LoginRequiredMixin, GenericCreateView):
    template_name = '%s/edit.html' % app_label
    fields = '__all__'
    model = Model
    success_url = reverse_lazy('%s:index' % app_label)
    success_message = '%(name)s ' + _('was created successfully')


class DeleteView(SuccessMessageMixin, LoginRequiredMixin, GenericDeleteView):
    template_name = '%s/delete.html' % app_label
    model = Model
    success_url = reverse_lazy('%s:index' % app_label)
    success_message = '%(name)s ' + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(DeleteView, self).delete(request, *args, **kwargs)
