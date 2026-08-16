from django.contrib.auth.mixins import LoginRequiredMixin
from sm.views import SafeDeleteMixin, GenericCSVExportView, GenericBulkDeleteView
from sm.mixins import MultiTenantMixin, BulkActionMixin

from .models import Model
from .forms import Form, FormDisabled
from . import app_label

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

from django.urls import reverse_lazy


class ListView(LoginRequiredMixin, MultiTenantMixin, BulkActionMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "name"


class DetailView(LoginRequiredMixin, MultiTenantMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(
    SuccessMessageMixin, LoginRequiredMixin, MultiTenantMixin, GenericUpdateView
):
    success_message = "%(name)s " + _("was updated successfully")
    model = Model

    template_name = "%s/edit.html" % app_label

    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(
    SuccessMessageMixin, LoginRequiredMixin, MultiTenantMixin, GenericCreateView
):
    success_message = "%(name)s " + _("was created successfully")

    template_name = "%s/edit.html" % app_label
    form_class = Form
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class DeleteView(
    SafeDeleteMixin, LoginRequiredMixin, MultiTenantMixin, GenericDeleteView
):
    success_message = "%(name)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class BulkDeleteView(GenericBulkDeleteView):
    model = Model


class CSVExportView(GenericCSVExportView):
    model = Model
    filename = "patchtime.csv"
    export_fields = [
        ("name", "name"),
    ]
