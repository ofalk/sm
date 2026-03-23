from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from sm.views import SafeDeleteMixin
from sm.mixins import MultiTenantMixin

from .models import Model
from .forms import Form, FormDisabled, BulkActionForm
from . import app_label

from django.views import View
from django.shortcuts import redirect

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView

from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

try:
    from django.urls import reverse_lazy
except Exception:  # pragma: no cover
    from django.urls import reverse_lazy  # pragma: no cover


class ListView(PermissionRequiredMixin, MultiTenantMixin, GenericListView):
    permission_required = "server.view_model"
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    # queryset = model.objects.all()
    ordering = "hostname"

    def get_queryset(self):
        queryset = super().get_queryset()
        if "srvmanager-show_disposed" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_disposed"] == "true":
                return queryset.order_by(self.ordering)
        return queryset.exclude(status__name="Disposed").order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulk_form"] = BulkActionForm()
        return context


class BulkActionView(PermissionRequiredMixin, MultiTenantMixin, View):
    permission_required = "server.change_model"

    def post(self, request, *args, **kwargs):
        server_ids = request.POST.getlist("selected_servers")
        if not server_ids:
            messages.warning(request, _("No servers selected."))
            return redirect("server:index")

        form = BulkActionForm(request.POST)
        if form.is_valid():
            # Use get_queryset to ensure multi-tenancy filtering
            servers = self.get_queryset().filter(id__in=server_ids)
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
            elif form.cleaned_data["status"]:
                new_status = form.cleaned_data["status"]
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


class DetailView(PermissionRequiredMixin, MultiTenantMixin, GenericUpdateView):
    permission_required = "server.view_model"
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(
    SuccessMessageMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericUpdateView,
):
    permission_required = "server.change_model"
    success_message = "%(hostname)s " + _("was updated successfully")
    model = Model

    template_name = "%s/edit.html" % app_label
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(
    SuccessMessageMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericCreateView,
):
    permission_required = "server.add_model"
    success_message = "%(hostname)s " + _("was created successfully")
    model = Model

    template_name = "%s/edit.html" % app_label
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class DeleteView(
    SafeDeleteMixin,
    PermissionRequiredMixin,
    MultiTenantMixin,
    GenericDeleteView,
):
    permission_required = "server.delete_model"
    success_message = "%(hostname)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class SearchView(PermissionRequiredMixin, MultiTenantMixin, GenericListView):
    permission_required = "server.view_model"
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "hostname"
