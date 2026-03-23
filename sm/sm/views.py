from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from server.models import Model as Server
from cluster.models import Model as Cluster
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.http import Http404, HttpResponseRedirect

from django.db.models import ProtectedError
from django.utils.translation import gettext as _
from django.shortcuts import redirect
from django.views import View
from typing import Any, List
from .utils_starterpack import import_starter_pack


class SafeDeleteMixin:
    """
    Mixin to catch ProtectedError during deletion and offer
    reassignment or bulk deletion.
    """

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)  # type: ignore
        if hasattr(self, "protected_error") and self.protected_error:  # type: ignore
            context["protected_error"] = True
            # Exclude our object from reassign list
            context["all_objects"] = self.model.objects.exclude(
                pk=self.object.pk  # type: ignore
            )

            # Re-collect protected objects properly
            try:
                self.object.delete()  # type: ignore
            except ProtectedError as e:
                context["protected_objects"] = e.protected_objects
                context["protected_count"] = len(e.protected_objects)
        return context

    def form_valid(self, form: Any) -> Any:
        success_url = self.get_success_url()  # type: ignore
        try:
            # Try normal deletion first
            obj_name = str(self.object)  # type: ignore
            self.object.delete()  # type: ignore
            if hasattr(self, "success_message") and self.success_message:  # type: ignore  # noqa: E501
                messages.success(
                    # type: ignore
                    self.request,
                    self.success_message % self.object.__dict__,
                )
            else:
                messages.success(self.request, _("Successfully deleted %s") % obj_name)
            return HttpResponseRedirect(success_url)
        except ProtectedError as e:
            action = self.request.POST.get("protected_action")
            if action == "reassign":
                new_obj_id = self.request.POST.get("new_target")
                if new_obj_id:
                    new_obj = self.model.objects.get(pk=new_obj_id)  # type: ignore
                    # This part is tricky as we don't know the field name on
                    # the remote side without inspecting the protected objects.
                    for protected in e.protected_objects:
                        # Find the FK field that points to our object
                        for field in protected._meta.fields:
                            # type: ignore
                            if field.is_relation and field.related_model == self.model:
                                setattr(protected, field.name, new_obj)
                                protected.save()

                    self.object.delete()  # type: ignore
                    messages.success(
                        self.request,
                        _("Successfully reassigned dependencies and deleted %s")
                        % self.object,  # type: ignore
                    )
                    return HttpResponseRedirect(success_url)

            elif action == "delete_all":
                for protected in e.protected_objects:
                    protected.delete()
                self.object.delete()  # type: ignore
                messages.success(
                    self.request,
                    _("Successfully deleted %s and all dependent objects")
                    % self.object,  # type: ignore
                )
                return HttpResponseRedirect(success_url)

            self.protected_error = True  # type: ignore
            return self.render_to_response(
                self.get_context_data(object=self.object)  # type: ignore
            )


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_queryset_filtered(self, model: Any) -> Any:
        if self.request.user.is_superuser:
            return model.objects.all()
        user_groups = self.request.user.groups.all()
        if hasattr(model, "group"):
            return model.objects.filter(
                Q(group__in=user_groups) | Q(group__isnull=True)
            )
        return model.objects.all()

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)

        # Basic Stats (Filtered)
        context["server_count"] = self.get_queryset_filtered(Server).count()
        context["cluster_count"] = self.get_queryset_filtered(Cluster).count()
        context["vendor_count"] = Vendor.objects.count()
        context["os_count"] = OS.objects.count()

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
        if self.request.user.is_superuser:
            return model.objects.all()
        user_groups = self.request.user.groups.all()
        if hasattr(model, "group"):
            return model.objects.filter(
                Q(group__in=user_groups) | Q(group__isnull=True)
            )
        return model.objects.all()

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
            context["vendors"] = Vendor.objects.filter(name__icontains=query)[:10]
            context["clusters"] = self.get_queryset_filtered(Cluster).filter(
                name__icontains=query
            )[:10]

            # Simple check if anything was found
            context["has_results"] = any(
                [
                    context["nav_results"],
                    context["servers"].exists(),
                    context["vendors"].exists(),
                    context["clusters"].exists(),
                ]
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
            record = model.history.get(history_id=history_id)  # type: ignore
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
