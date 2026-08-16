from django.contrib.auth.mixins import LoginRequiredMixin
from sm.views import SafeDeleteMixin, GenericCSVExportView
from sm.mixins import MultiTenantMixin, filter_queryset_by_tenant

from .models import Model
from .forms import Form, FormDisabled
from . import app_label

from vendor.models import Model as VendorModel
from django.db.models import Prefetch
from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

from django.urls import reverse_lazy


class ListView(LoginRequiredMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    # Grouped list: rows are Vendors (with their servermodels prefetched), so
    # the queryset model is the Vendor model, not this app's own Model.
    model = VendorModel
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "name"

    def get_queryset(self):
        qs = filter_queryset_by_tenant(VendorModel.objects.all(), self.request).filter(
            is_hardware=True
        )
        servermodels = filter_queryset_by_tenant(Model.objects.all(), self.request)
        qs = qs.prefetch_related(Prefetch("servermodel_set", queryset=servermodels))
        if "srvmanager-show_empty" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_empty"] == "false":
                return qs.exclude(servermodel=None).order_by("name")
        return qs.order_by("name")


class DetailView(LoginRequiredMixin, MultiTenantMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(
    SuccessMessageMixin, LoginRequiredMixin, MultiTenantMixin, GenericUpdateView
):
    success_message = "%(name)s " + _("was updated successfully")

    template_name = "%s/edit.html" % app_label
    model = Model

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

    def get_initial(self):
        from vendor.models import Model as VendorModel

        initial = super().get_initial()
        if "vendor" in self.kwargs:
            vendor_qs = VendorModel.objects.filter(pk=self.kwargs["vendor"])
            if hasattr(self, "request"):
                vendor_qs = filter_queryset_by_tenant(vendor_qs, self.request)
            initial["vendor"] = vendor_qs.first()
        return initial


class DeleteView(
    SafeDeleteMixin, LoginRequiredMixin, MultiTenantMixin, GenericDeleteView
):
    success_message = "%(name)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class CSVExportView(GenericCSVExportView):
    model = Model
    filename = "servermodel.csv"
    export_fields = [
        ("name", "name"),
        ("vendor", "vendor__name"),
    ]
