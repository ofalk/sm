from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from server.models import Model as Server
from cluster.models import Model as Cluster
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.http import Http404

from django.db.models import ProtectedError
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect


class SafeDeleteMixin:
    """
    Mixin to catch ProtectedError during deletion and offer
    reassignment or bulk deletion.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "protected_error") and self.protected_error:
            context["protected_error"] = True
            context["all_objects"] = self.model.objects.exclude(pk=self.object.pk)

            # Re-collect protected objects properly
            try:
                self.object.delete()
            except ProtectedError as e:
                context["protected_objects"] = e.protected_objects
                context["protected_count"] = len(e.protected_objects)
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            # Try normal deletion first
            obj_name = str(self.object)
            self.object.delete()
            if hasattr(self, "success_message") and self.success_message:
                messages.success(
                    self.request, self.success_message % self.object.__dict__
                )
            else:
                messages.success(self.request, _("Successfully deleted %s") % obj_name)
            return HttpResponseRedirect(success_url)
        except ProtectedError as e:
            action = self.request.POST.get("protected_action")
            if action == "reassign":
                new_obj_id = self.request.POST.get("new_target")
                if new_obj_id:
                    new_obj = self.model.objects.get(pk=new_obj_id)
                    # This part is tricky as we don't know the field name on
                    # the remote side without inspecting the protected objects.
                    for protected in e.protected_objects:
                        # Find the FK field that points to our object
                        for field in protected._meta.fields:
                            if field.is_relation and field.related_model == self.model:
                                setattr(protected, field.name, new_obj)
                                protected.save()

                    self.object.delete()
                    messages.success(
                        self.request,
                        _("Successfully reassigned dependencies and deleted %s")
                        % self.object,
                    )
                    return HttpResponseRedirect(success_url)

            elif action == "delete_all":
                for protected in e.protected_objects:
                    protected.delete()
                self.object.delete()
                messages.success(
                    self.request,
                    _("Successfully deleted %s and all dependent objects")
                    % self.object,
                )
                return HttpResponseRedirect(success_url)

            self.protected_error = True
            return self.render_to_response(self.get_context_data(object=self.object))


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basic Stats
        context["server_count"] = Server.objects.count()
        context["cluster_count"] = Cluster.objects.count()
        context["vendor_count"] = Vendor.objects.count()
        context["os_count"] = OS.objects.count()

        # Data for Charts
        # OS Distribution
        os_dist = (
            Server.objects.values(
                "operatingsystem__vendor__name", "operatingsystem__version"
            )
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
            Server.objects.values("status__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        context["status_labels"] = [item["status__name"] for item in status_dist]
        context["status_data"] = [item["count"] for item in status_dist]

        # Recent Activity
        context["recent_servers"] = Server.objects.all().order_by("-id")[:5]

        return context


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search.html"

    def get_template_names(self):
        if self.request.GET.get("ajax"):
            return ["search_results_ajax.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").lower()
        context["query"] = query

        # Navigation Quick Jumps
        nav_targets = [
            {"name": "Dashboard", "url": "/", "icon": "fa-gauge-high"},
            {"name": "Servers", "url": "/server/", "icon": "fa-server"},
            {"name": "Server Models", "url": "/servermodel/", "icon": "fa-cubes"},
            {"name": "Vendors", "url": "/vendor/", "icon": "fa-industry"},
            {"name": "Clusters", "url": "/cluster/", "icon": "fa-th-large"},
            {
                "name": "Operating Systems",
                "url": "/operatingsystem/",
                "icon": "fa-laptop",
            },
            {"name": "Statuses", "url": "/status/", "icon": "fa-tag"},
            {"name": "Locations", "url": "/location/", "icon": "fa-map-marker-alt"},
            {"name": "Domains", "url": "/domain/", "icon": "fa-globe"},
            {"name": "Patch Times", "url": "/patchtime/", "icon": "fa-calendar"},
            {
                "name": "Cluster Software",
                "url": "/clustersoftware/",
                "icon": "fa-shield-halved",
            },
            {
                "name": "Cluster Packages",
                "url": "/clusterpackage/",
                "icon": "fa-archive",
            },
            {
                "name": "API Documentation",
                "url": "/api/schema/swagger-ui/",
                "icon": "fa-book",
            },
        ]

        if len(query) >= 2:
            # Filter navigation targets
            context["nav_results"] = [
                item for item in nav_targets if query in (item["name"].lower())
            ]

            context["servers"] = Server.objects.filter(hostname__icontains=query)[:10]
            context["vendors"] = Vendor.objects.filter(name__icontains=query)[:10]
            context["clusters"] = Cluster.objects.filter(name__icontains=query)[:10]

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app_label = kwargs.get("app_label")
        history_id = kwargs.get("history_id")

        try:
            model = apps.get_model(app_label, "Model")
            record = model.history.get(history_id=history_id)
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


class TermsView(TemplateView):
    template_name = "legal/terms.html"


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"
