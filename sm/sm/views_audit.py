from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView
from typing import Any

from .utils_permissions import APP_MODELS


class AuditLogView(LoginRequiredMixin, ListView):
    """
    Per-tenant audit log: lists history records across all core models,
    filtered by the user's groups (or a specific selected group).
    """

    template_name = "audit_log.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_group(self):
        group_id = self.request.GET.get("group")
        if not group_id or not group_id.isdigit():
            return None
        return int(group_id)

    def get_queryset(self):
        user = self.request.user
        group_filter = self.get_group()

        entries = []
        for app_label, _model_name in APP_MODELS:
            try:
                from django.apps import apps

                model = apps.get_model(app_label, "Model")
            except LookupError:
                continue
            if not hasattr(model, "history"):
                continue

            qs = model.history.all()
            if not user.is_superuser:
                user_groups = user.groups.all()
                qs = qs.filter(Q(group_id__in=user_groups) | Q(group_id__isnull=True))
            if group_filter:
                qs = qs.filter(group_id=group_filter)

            for record in qs.select_related("history_user")[:100]:
                entries.append(
                    {
                        "date": record.history_date,
                        "user": (
                            record.history_user
                            if getattr(record, "history_user_id", None)
                            else None
                        ),
                        "user_id": getattr(record, "history_user_id", None),
                        "action": record.history_type,
                        "model": model._meta.verbose_name,
                        "object": record,
                        "group_id": getattr(record, "group_id", None),
                        "group_name": (
                            record.group.name
                            if getattr(record, "group_id", None) and record.group_id
                            else None
                        ),
                    }
                )

        entries.sort(key=lambda e: e["date"], reverse=True)
        return entries

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser:
            from django.contrib.auth.models import Group

            context["groups"] = Group.objects.all()
        else:
            context["groups"] = user.groups.all()
        context["selected_group"] = self.get_group()
        return context
