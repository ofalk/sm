import logging

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from server.models import Model as Server
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from clusterpackagetype.models import Model as ClusterPackageType
from clustersoftware.models import Model as ClusterSoftware
from domain.models import Model as Domain
from location.models import Model as Location
from operatingsystem.models import Model as OS
from patchtime.models import Model as Patchtime
from servermodel.models import Model as ServerModel
from status.models import Model as Status
from vendor.models import Model as Vendor
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.http import Http404, JsonResponse
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from django.db.models import ProtectedError
from django.utils.translation import gettext as _
from django.shortcuts import redirect
from django.views import View
from typing import Any, List
from .mixins import filter_queryset_by_tenant, filter_history_queryset_by_tenant
from .utils_starterpack import import_starter_pack

logger = logging.getLogger(__name__)


class SafeDeleteMixin:
    """
    Mixin to catch ProtectedError during deletion and show a friendly
    message instead of raising a 500 error.
    """

    def form_valid(self, form: Any) -> Any:
        try:
            obj_name = str(self.object)  # type: ignore
            # Chain to the rest of the MRO (e.g. MultiTenantMixin) so tenant
            # guards such as read-only global fixtures are enforced.
            response = super().form_valid(form)  # type: ignore
            if hasattr(self, "success_message") and self.success_message:  # type: ignore  # noqa: E501
                messages.success(
                    # type: ignore
                    self.request,
                    self.success_message % self.object.__dict__,
                )
            else:
                messages.success(self.request, _("Successfully deleted %s") % obj_name)
            return response
        except ProtectedError as e:
            instances = ", ".join(str(obj) for obj in e.protected_objects)
            messages.error(
                self.request,
                _(
                    "%(name)s cannot be deleted because it is referenced by "
                    "%(count)d other resource(s): %(instances)s"
                )
                % {
                    "name": self.object,  # type: ignore
                    "count": len(e.protected_objects),
                    "instances": instances,
                },
            )
            return self.render_to_response(
                self.get_context_data(object=self.object)  # type: ignore
            )


class GenericBulkDeleteView(LoginRequiredMixin, View):
    """
    Generic bulk-delete view for models that use the standard
    ``MultiTenantMixin`` list pattern.

    Subclasses must define ``model`` and the request must include
    ``selected_ids`` (a list of primary keys). Deletion runs through the
    tenant-filtered queryset so users can only ever delete their own items.
    """

    model = None

    def get_queryset(self) -> Any:
        queryset = self.model.objects.all()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        selected_groups = self.request.session.get("selected_groups", [])
        if hasattr(self.model, "group"):
            if selected_groups:
                group_ids = [int(g) for g in selected_groups if g.isdigit()]
                if group_ids:
                    return queryset.filter(
                        Q(group__id__in=group_ids) | Q(group__isnull=True)
                    )
            return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))
        return queryset

    def get_success_url(self) -> str:
        return reverse("%s:index" % self.model._meta.app_label)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        ids = request.POST.getlist("selected_ids")
        if not ids:
            messages.warning(request, _("No items selected."))
            return redirect(self.get_success_url())

        model_name = self.model._meta.object_name.lower()
        app_label = self.model._meta.app_label
        delete_perm = "delete_%s" % model_name
        if not request.user.has_perm("{}.{}".format(app_label, delete_perm)):
            raise PermissionDenied

        queryset = self.get_queryset().filter(pk__in=ids)
        count = queryset.count()
        if count == 0:
            messages.warning(request, _("No items selected."))
            return redirect(self.get_success_url())

        try:
            queryset.delete()
            messages.success(
                request,
                _("Successfully deleted %d item(s).") % count,
            )
        except ProtectedError as e:
            instances = ", ".join(str(obj) for obj in list(e.protected_objects)[:5])
            messages.error(
                request,
                _("Some items cannot be deleted because they are referenced by: %s")
                % instances,
            )
        return redirect(self.get_success_url())


class GenericCSVExportView(LoginRequiredMixin, View):
    """
    Exports the model's rows (tenant-filtered) as CSV.

    Subclasses define ``model`` and ``export_fields`` — an ordered list of
    ``(header, attribute_path)`` tuples. Attribute paths may traverse related
    objects with ``__``.
    """

    model = None
    export_fields: List = []
    filename = "export.csv"

    def get_queryset(self) -> Any:
        queryset = self.model.objects.all()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        selected_groups = self.request.session.get("selected_groups", [])
        if hasattr(self.model, "group"):
            if selected_groups:
                group_ids = [int(g) for g in selected_groups if g.isdigit()]
                if group_ids:
                    return queryset.filter(
                        Q(group__id__in=group_ids) | Q(group__isnull=True)
                    )
            return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))
        return queryset

    def get_filename(self) -> str:
        return self.filename

    def resolve_value(self, obj: Any, path: str) -> Any:
        value: Any = obj
        for part in path.split("__"):
            if value is None:
                return ""
            try:
                value = getattr(value, part)
            except (AttributeError, ObjectDoesNotExist):
                return ""
        return value

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="%s"' % self.get_filename()
        )

        writer = csv.writer(response)
        writer.writerow([header for header, _ in self.export_fields])
        for obj in self.get_queryset():
            writer.writerow(
                [self.resolve_value(obj, path) for _, path in self.export_fields]
            )
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_queryset_filtered(self, model: Any) -> Any:
        if not hasattr(model, "group"):
            return model.objects.all()
        return filter_queryset_by_tenant(model.objects.all(), self.request)

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)

        # Basic Stats (Filtered)
        context["server_count"] = self.get_queryset_filtered(Server).count()
        context["cluster_count"] = self.get_queryset_filtered(Cluster).count()
        context["vendor_count"] = self.get_queryset_filtered(Vendor).count()
        context["os_count"] = self.get_queryset_filtered(OS).count()

        # Data for Charts (Filtered)
        # OS Distribution
        os_dist = (
            self.get_queryset_filtered(Server)
            .values("operatingsystem__vendor__name", "operatingsystem__version")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        context["os_labels"] = [
            f"{item['operatingsystem__vendor__name']} "
            f"{item['operatingsystem__version']}"
            for item in os_dist
        ]
        context["os_data"] = [item["count"] for item in os_dist]

        # Status Distribution
        status_dist = (
            self.get_queryset_filtered(Server)
            .values("status__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        context["status_labels"] = [item["status__name"] for item in status_dist]
        context["status_data"] = [item["count"] for item in status_dist]

        # Recent Activity (Filtered)
        context["recent_servers"] = (
            self.get_queryset_filtered(Server).all().order_by("-id")[:5]
        )

        return context


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search.html"

    def get_queryset_filtered(self, model: Any) -> Any:
        if not hasattr(model, "group"):
            return model.objects.all()
        return filter_queryset_by_tenant(model.objects.all(), self.request)

    def get_template_names(self) -> List[str]:
        if self.request.GET.get("ajax"):
            return ["search_results_ajax.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").lower()
        context["query"] = query

        # Navigation Quick Jumps
        nav_targets = [
            {"name": _("Dashboard"), "url": "/", "icon": "fa-gauge-high"},
            {
                "name": _("Group Management"),
                "url": "/group/members/",
                "icon": "fa-users",
            },
            {"name": _("Servers"), "url": "/server/", "icon": "fa-server"},
            {"name": _("Server Models"), "url": "/servermodel/", "icon": "fa-cubes"},
            {"name": _("Vendors"), "url": "/vendor/", "icon": "fa-industry"},
            {"name": _("Clusters"), "url": "/cluster/", "icon": "fa-th-large"},
            {
                "name": _("Operating Systems"),
                "url": "/operatingsystem/",
                "icon": "fa-laptop",
            },
            {"name": _("Statuses"), "url": "/status/", "icon": "fa-tag"},
            {"name": _("Locations"), "url": "/location/", "icon": "fa-map-marker-alt"},
            {"name": _("Domains"), "url": "/domain/", "icon": "fa-globe"},
            {"name": _("Patch Times"), "url": "/patchtime/", "icon": "fa-calendar"},
            {
                "name": _("Cluster Software"),
                "url": "/clustersoftware/",
                "icon": "fa-shield-halved",
            },
            {
                "name": _("Cluster Packages"),
                "url": "/clusterpackage/",
                "icon": "fa-archive",
            },
            {
                "name": _("API Documentation"),
                "url": "/api/schema/swagger-ui/",
                "icon": "fa-book",
            },
        ]

        if len(query) >= 2:
            # Filter navigation targets
            context["nav_results"] = [
                item for item in nav_targets if query in (item["name"].lower())
            ]

            context["servers"] = self.get_queryset_filtered(Server).filter(
                hostname__icontains=query
            )[:10]
            context["vendors"] = self.get_queryset_filtered(Vendor).filter(
                name__icontains=query
            )[:10]
            context["clusters"] = self.get_queryset_filtered(Cluster).filter(
                name__icontains=query
            )[:10]
            context["domains"] = self.get_queryset_filtered(Domain).filter(
                name__icontains=query
            )[:10]
            context["locations"] = self.get_queryset_filtered(Location).filter(
                name__icontains=query
            )[:10]
            context["statuses"] = self.get_queryset_filtered(Status).filter(
                name__icontains=query
            )[:10]
            context["patchtimes"] = self.get_queryset_filtered(Patchtime).filter(
                name__icontains=query
            )[:10]
            context["servermodels"] = self.get_queryset_filtered(ServerModel).filter(
                name__icontains=query
            )[:10]
            context["os"] = self.get_queryset_filtered(OS).filter(
                version__icontains=query
            )[:10]
            context["clustersoftware"] = self.get_queryset_filtered(
                ClusterSoftware
            ).filter(Q(name__icontains=query) | Q(version__icontains=query))[:10]
            context["clusterpackagetypes"] = self.get_queryset_filtered(
                ClusterPackageType
            ).filter(name__icontains=query)[:10]
            context["clusterpackages"] = self.get_queryset_filtered(
                ClusterPackage
            ).filter(name__icontains=query)[:10]

            # Simple check if anything was found
            result_lists = [
                context["servers"],
                context["vendors"],
                context["clusters"],
                context["domains"],
                context["locations"],
                context["statuses"],
                context["patchtimes"],
                context["servermodels"],
                context["os"],
                context["clustersoftware"],
                context["clusterpackagetypes"],
                context["clusterpackages"],
            ]
            context["has_results"] = bool(context["nav_results"]) or any(
                rl.exists() for rl in result_lists if hasattr(rl, "exists")
            )
        else:
            context["has_results"] = False
            context["query_too_short"] = True

        return context


class HistoryDiffView(LoginRequiredMixin, TemplateView):
    template_name = "history_diff.html"

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        app_label = kwargs.get("app_label")
        history_id = kwargs.get("history_id")

        try:
            model = apps.get_model(app_label, "Model")
            history_qs = filter_history_queryset_by_tenant(
                model.history.all(), self.request  # type: ignore
            )
            record = history_qs.get(history_id=history_id)
        except (LookupError, ObjectDoesNotExist):
            raise Http404("History record not found")

        context["record"] = record
        context["instance"] = record.instance
        context["app_label"] = app_label

        if record.prev_record:
            context["diff"] = record.diff_against(record.prev_record)
        else:
            context["diff"] = None

        return context


class PatchScheduleView(LoginRequiredMixin, TemplateView):
    """
    Overview of servers grouped by their patch-time window, so operators can
    see at a glance what is patched when.
    """

    template_name = "patch_schedule.html"

    def get_servers(self) -> Any:
        if self.request.user.is_superuser:
            return Server.objects.all()
        user_groups = self.request.user.groups.all()
        selected_groups = self.request.session.get("selected_groups", [])
        if selected_groups:
            group_ids = [int(g) for g in selected_groups if g.isdigit()]
            if group_ids:
                return Server.objects.filter(
                    Q(group__id__in=group_ids) | Q(group__isnull=True)
                )
        return Server.objects.filter(Q(group__in=user_groups) | Q(group__isnull=True))

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        servers = self.get_servers().select_related("patchtime", "status")
        by_window: dict = {}
        for server in servers:
            window = server.patchtime.name if server.patchtime_id else _("Unassigned")
            by_window.setdefault(window, []).append(server)

        ordered = sorted(
            by_window.items(), key=lambda item: (item[0] == _("Unassigned"), item[0])
        )
        context["windows"] = ordered
        context["server_count"] = servers.count()
        return context


class ImportStarterPackView(LoginRequiredMixin, View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        user_groups = request.user.groups.all()
        if not user_groups.exists():
            messages.error(request, _("You are not assigned to any group."))
            return redirect("dashboard")

        group = user_groups.first()
        results = import_starter_pack(group)

        messages.success(
            request,
            _("Imported %d vendors and %d operating systems into group %s.")
            % (results["vendors"], results["os"], group.name),
        )
        return redirect("vendor:index")


class TermsView(TemplateView):
    template_name = "legal/terms.html"


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"


class HealthView(View):
    def get(self, request: Any, *args: Any, **kwargs: Any) -> JsonResponse:
        health = {
            "status": "healthy",
            "version": getattr(settings, "APP_VERSION", "unknown"),
            "last_modification": getattr(settings, "APP_MODIFICATION_DATE", "unknown"),
            "checks": {},
        }

        # Check database connection
        try:
            from django.db import connection

            connection.cursor()
            health["checks"]["database"] = "ok"
        except Exception:
            # Log the real error server-side; never leak connection internals
            # (host/port/user) to unauthenticated callers.
            logger.exception("Health check: database connection failed")
            health["status"] = "unhealthy"
            health["checks"]["database"] = "unavailable"

        status_code = 200 if health["status"] == "healthy" else 503
        return JsonResponse(health, status=status_code)
