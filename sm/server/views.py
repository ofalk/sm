from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from sm.views import SafeDeleteMixin, GenericCSVExportView
from sm.mixins import filter_queryset_by_tenant, MultiTenantMixin, BulkActionMixin

from .models import Model
from .forms import Form, FormDisabled, BulkActionForm
from . import app_label

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.utils import timezone

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
    # queryset = model.objects.all()
    ordering = "hostname"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "status",
                "location",
                "domain",
                "patchtime",
                "servermodel",
                "operatingsystem__vendor",
            )
        )
        if "srvmanager-show_disposed" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_disposed"] == "true":
                return queryset.order_by(self.ordering)
        return queryset.exclude(status__name="Disposed").order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulk_form"] = BulkActionForm()
        return context


class BulkActionView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        server_ids = request.POST.getlist("selected_ids")
        if not server_ids:
            messages.warning(request, _("No servers selected."))
            return redirect("server:index")

        form = BulkActionForm(request.POST)
        if form.is_valid():
            # Filter by tenant so a user can never bulk-operate on another
            # group's servers.
            servers = filter_queryset_by_tenant(Model.objects.all(), request).filter(
                id__in=server_ids
            )
            # Global (group-less) seed fixtures are read-only for tenant users
            if not request.user.is_superuser:
                servers = servers.exclude(group__isnull=True)
            count = servers.count()

            if form.cleaned_data["delete"]:
                # Check delete permission
                if not request.user.has_perm("server.delete_model"):
                    messages.error(
                        request,
                        _("You don't have permission to delete servers."),
                    )
                    return redirect("server:index")
                servers.delete()
                messages.success(request, _("Successfully deleted %d servers.") % count)
            elif form.cleaned_data["decommission"]:
                if not request.user.has_perm("server.change_model"):
                    messages.error(
                        request,
                        _("You don't have permission to change servers."),
                    )
                    return redirect("server:index")
                decommissioned = 0
                for server in servers:
                    if server.decommission_date is None:
                        server.decommission_date = timezone.localdate()
                        server.save()
                        decommissioned += 1
                messages.success(
                    request,
                    _("Successfully decommissioned %d servers.") % decommissioned,
                )
            elif form.cleaned_data["status"]:
                # Check change permission before re-labelling any servers.
                if not request.user.has_perm("server.change_model"):
                    messages.error(
                        request,
                        _("You don't have permission to change servers."),
                    )
                    return redirect("server:index")
                new_status = form.cleaned_data["status"]
                with transaction.atomic():
                    for server in servers:
                        server.status = new_status
                        server.save()
                messages.success(
                    request,
                    _("Successfully updated status to %s for %d servers.")
                    % (new_status, count),
                )
            else:
                messages.info(request, _("No action performed."))

        return redirect("server:index")


class DecommissionView(LoginRequiredMixin, MultiTenantMixin, View):
    """Marks a single server as decommissioned (sets the decommission date)."""

    def post(self, request, *args, **kwargs):
        server = get_object_or_404(Model, pk=kwargs.get("pk"))
        if not request.user.has_perm("server.change_model"):
            messages.error(request, _("You don't have permission to change servers."))
            return redirect("server:index")
        server.decommission_date = timezone.localdate()
        server.save()
        messages.success(
            request,
            _("%(hostname)s has been decommissioned.") % {"hostname": server.hostname},
        )
        return redirect("server:index")


class RestoreView(LoginRequiredMixin, MultiTenantMixin, View):
    """Clears the decommission date, bringing a server back into use."""

    def post(self, request, *args, **kwargs):
        server = get_object_or_404(Model, pk=kwargs.get("pk"))
        if not request.user.has_perm("server.change_model"):
            messages.error(request, _("You don't have permission to change servers."))
            return redirect("server:index")
        server.decommission_date = None
        server.save()
        messages.success(
            request,
            _("%(hostname)s has been restored.") % {"hostname": server.hostname},
        )
        return redirect("server:index")


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
    success_message = "%(hostname)s " + _("was updated successfully")
    model = Model

    template_name = "%s/edit.html" % app_label
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    MultiTenantMixin,
    GenericCreateView,
):
    success_message = "%(hostname)s " + _("was created successfully")
    model = Model

    template_name = "%s/edit.html" % app_label
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class DeleteView(
    SafeDeleteMixin,
    LoginRequiredMixin,
    MultiTenantMixin,
    GenericDeleteView,
):
    success_message = "%(hostname)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class SearchView(LoginRequiredMixin, MultiTenantMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "hostname"


class CSVExportView(GenericCSVExportView):
    model = Model
    filename = "server.csv"
    export_fields = [
        ("hostname", "hostname"),
        ("status", "status__name"),
        ("domain", "domain__name"),
        ("location", "location__name"),
        ("application", "application"),
        ("rack", "rack"),
        ("primary_ip", "primary_ip"),
        ("management_ip", "management_ip"),
        ("description", "description"),
        ("decommission_date", "decommission_date"),
        ("tags", "tags.names"),
    ]
