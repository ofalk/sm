from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from sm.views import SafeDeleteMixin
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


class ListView(PermissionRequiredMixin, MultiTenantMixin, GenericListView):
    permission_required = "operatingsystem.view_model"
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "vendor"

    def get_queryset(self) -> Any:
        from vendor.models import Model as VendorModel

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


class DetailView(PermissionRequiredMixin, MultiTenantMixin, GenericUpdateView):
    permission_required = "operatingsystem.view_model"
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(
    SuccessMessageMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericUpdateView,
):
    permission_required = "operatingsystem.change_model"
    success_message = "%(version)s " + _("was updated successfully")
    template_name = "%s/edit.html" % app_label
    model = Model
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(
    SuccessMessageMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericCreateView,
):
    permission_required = "operatingsystem.add_model"
    success_message = "%(version)s " + _("was created successfully")

    template_name = "%s/edit.html" % app_label
    form_class = Form
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def get_initial(self) -> Any:
        from vendor.models import Model as VendorModel

        initial = super().get_initial()
        if "vendor" in self.kwargs:
            initial["vendor"] = VendorModel.objects.filter(
                pk=self.kwargs["vendor"]
            ).first()
        return initial


class DeleteView(
    SafeDeleteMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericDeleteView,
):
    permission_required = "operatingsystem.delete_model"
    success_message = "%(version)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)
