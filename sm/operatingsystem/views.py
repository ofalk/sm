from django.contrib.auth.mixins import LoginRequiredMixin

from sm.views import SafeDeleteMixin, GenericCSVExportView
from sm.mixins import MultiTenantMixin
from typing import Any

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

from vendor.models import Model as VendorModel


class ListView(LoginRequiredMixin, MultiTenantMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    # Grouped list: rows are Vendors (with their operating systems prefetched),
    # so the queryset model is the Vendor model. Permission checks stay
    # anchored to this app via ``permission_model``.
    model = VendorModel
    permission_model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "vendor"

    def get_queryset(self) -> Any:
        # Filtering by group is handled by MultiTenantMixin
        # (via super().get_queryset())
        # But we need the vendor grouping logic
        qs = VendorModel.objects.filter(
            is_software=True, group__in=self.request.user.groups.all()
        )
        if self.request.user.is_superuser:
            qs = VendorModel.objects.filter(is_software=True)

        if "srvmanager-show_empty" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_empty"] == "false":
                return qs.exclude(operatingsystem=None).order_by("name")
        return qs.order_by("name")


class DetailView(LoginRequiredMixin, MultiTenantMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    MultiTenantMixin,
    GenericUpdateView,
):
    success_message = "%(version)s " + _("was updated successfully")
    template_name = "%s/edit.html" % app_label
    model = Model
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    MultiTenantMixin,
    GenericCreateView,
):
    success_message = "%(version)s " + _("was created successfully")

    template_name = "%s/edit.html" % app_label
    form_class = Form
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def get_initial(self) -> Any:
        initial = super().get_initial()
        if "vendor" in self.kwargs:
            initial["vendor"] = VendorModel.objects.filter(
                pk=self.kwargs["vendor"]
            ).first()
        return initial


class DeleteView(
    SafeDeleteMixin,
    LoginRequiredMixin,
    MultiTenantMixin,
    GenericDeleteView,
):
    success_message = "%(version)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class CSVExportView(GenericCSVExportView):
    model = Model
    filename = "operatingsystem.csv"
    export_fields = [
        ("version", "version"),
        ("vendor", "vendor__name"),
    ]
