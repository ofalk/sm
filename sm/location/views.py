from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Location
from . forms import LocationForm, LocationFormDisabled

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy

from django.contrib import messages


class LocationListView(LoginRequiredMixin, ListView):
    template_name = 'location/list.html'
    model = Location
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'name'


class LocationDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'location/detail.html'
    model = Location
    form_class = LocationFormDisabled


class LocationUpdateView(LocationDetailView, SuccessMessageMixin):
    template_name = 'location/edit.html'
    form_class = LocationForm
    success_url = reverse_lazy('location:index')
    success_message = "%(name)s" + _('was updated successfully')


class LocationCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'location/edit.html'
    fields = '__all__'
    model = Location
    success_url = reverse_lazy('location:index')
    success_message = "%(name)s " + _('was created successfully')


class LocationDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'location/delete.html'
    model = Location
    success_url = reverse_lazy('location:index')
    success_message = "%(name)s " + _('was deleted successfully')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(LocationDeleteView, self).delete(request, *args, **kwargs)
