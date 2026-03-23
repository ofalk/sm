from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext as _
from typing import Any
from django.db.models.query import QuerySet
from django.forms import ModelForm


class MultiTenantMixin:
    """
    Mixin to filter querysets by user groups and auto-assign group on save.
    Enforces item quotas per group.
    """

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()  # type: ignore
        if self.request.user.is_superuser:
            return queryset

        user_groups = self.request.user.groups.all()
        return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))

    def check_quota(self, group: Any) -> bool:
        if not group or not hasattr(group, "profile"):
            return True

        profile = group.profile
        max_items = profile.max_items

        # Count items across models
        from server.models import Model as Server
        from cluster.models import Model as Cluster
        from domain.models import Model as Domain
        from vendor.models import Model as Vendor
        from operatingsystem.models import Model as OS

        count = (
            Server.objects.filter(group=group).count()
            + Cluster.objects.filter(group=group).count()
            + Domain.objects.filter(group=group).count()
            + Vendor.objects.filter(group=group).count()
            + OS.objects.filter(group=group).count()
        )

        if count >= max_items:
            return False
        return True

    def form_valid(self, form: ModelForm) -> Any:
        # Auto-assign first group if not set and not superuser
        if not form.instance.group and not self.request.user.is_superuser:
            user_groups = self.request.user.groups.all()
            if user_groups.exists():
                form.instance.group = user_groups.first()

        # Check quota for NEW items
        if not form.instance.pk:
            if not self.check_quota(form.instance.group):
                quota_limit = 0
                if form.instance.group and hasattr(form.instance.group, "profile"):
                    quota_limit = form.instance.group.profile.max_items
                messages.error(
                    self.request,
                    _("Quota exceeded for this group (%d items).") % quota_limit,
                )
                return self.form_invalid(form)

        # Call super().form_valid(form) to let other mixins (like SuccessMessageMixin)
        # or the base view handle the actual saving and response.
        return super().form_valid(form)  # type: ignore


class APIMultiTenantMixin:
    """
    Mixin for DRF ViewSets to filter by user groups and auto-assign on create.
    """

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()  # type: ignore
        if self.request.user.is_superuser:
            return queryset

        user_groups = self.request.user.groups.all()
        return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))

    def perform_create(self, serializer: Any) -> None:
        user_groups = self.request.user.groups.all()
        group = user_groups.first() if user_groups.exists() else None

        if not self.request.user.is_superuser:
            # Simple quota check for API
            if group and hasattr(group, "profile"):
                from server.models import Model as Server
                from cluster.models import Model as Cluster
                from domain.models import Model as Domain
                from vendor.models import Model as Vendor
                from operatingsystem.models import Model as OS

                count = (
                    Server.objects.filter(group=group).count()
                    + Cluster.objects.filter(group=group).count()
                    + Domain.objects.filter(group=group).count()
                    + Vendor.objects.filter(group=group).count()
                    + OS.objects.filter(group=group).count()
                )
                if count >= group.profile.max_items:
                    from rest_framework.exceptions import ValidationError

                    raise ValidationError(_("Quota exceeded for this group."))

            serializer.save(group=group)
        else:
            serializer.save()
