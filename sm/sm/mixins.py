from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext as _
from typing import Any, Optional
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.contrib.auth.models import Group
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError
from .forms import BulkActionForm


def required_permission_codename(view: Any) -> str:
    """
    Returns the ``add``/``change``/``delete`` permission suffix a view type
    requires (``"view"`` for everything else, e.g. list/detail/search).
    """
    if isinstance(view, DeleteView):
        return "delete"
    if isinstance(view, UpdateView):
        return "change"
    if isinstance(view, CreateView):
        return "add"
    return "view"


def get_accessible_group_ids(request: Any) -> Optional[list[int]]:
    """
    Returns the group IDs a user may query, based on their session-selected
    groups -- but ONLY for groups the user is actually a member of.

    Selected groups that don't belong to the user are dropped so a user can
    never read another tenant's data by tampering with the session.

    Returns None if no selection is active (callers then fall back to the
    user's own groups). If the user's active selection contains no group they
    belong to (e.g. a tampered session), it falls back to None as well so the
    caller shows only the user's own groups -- never another tenant's data.
    """
    user_groups = request.user.groups.all()
    user_group_ids = set(user_groups.values_list("id", flat=True))

    selected = request.session.get("selected_groups", [])
    if not selected:
        return None

    accessible = [int(g) for g in selected if g.isdigit() and int(g) in user_group_ids]
    # A selection that sanitizes down to nothing means the user only picked
    # groups they don't belong to; fall back to their own groups.
    return accessible or None


def filter_queryset_by_tenant(queryset: QuerySet, request: Any) -> QuerySet:
    """
    Filters a queryset so the requesting user only sees data belonging to
    their groups (or global items with no group). Superusers see everything.
    Session-selected groups are honored but sanitized to groups the user
    actually belongs to, so a user can never read another tenant's data.
    """
    if request.user.is_superuser:
        return queryset

    user_groups = request.user.groups.all()
    accessible_group_ids = get_accessible_group_ids(request)

    if accessible_group_ids is not None:
        return queryset.filter(
            Q(group__id__in=accessible_group_ids) | Q(group__isnull=True)
        )

    return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))


def filter_queryset_for_user(queryset: QuerySet, user: Any) -> QuerySet:
    """
    Filters a queryset to only items the user may reference (their groups plus
    global/group-less rows). Unlike ``filter_queryset_by_tenant`` this takes a
    plain user (no request/session) so it can be used when building forms.
    """
    if user is not None and getattr(user, "is_superuser", False):
        return queryset
    user_groups = user.groups.all() if user is not None else Group.objects.none()
    return queryset.filter(Q(group__in=user_groups) | Q(group__isnull=True))


def filter_history_queryset_by_tenant(history_qs: QuerySet, request: Any) -> QuerySet:
    """
    Filters a simple-history queryset by the requesting user's groups (plus
    global/group-less entries). Superusers see everything. Uses the same
    sanitized group selection as ``filter_queryset_by_tenant``.
    """
    if request.user.is_superuser:
        return history_qs

    user_groups = request.user.groups.all()
    accessible_group_ids = get_accessible_group_ids(request)
    group_ids = (
        accessible_group_ids
        if accessible_group_ids is not None
        else list(user_groups.values_list("id", flat=True))
    )

    if not group_ids:
        return history_qs.none()

    return history_qs.filter(Q(group_id__in=group_ids) | Q(group_id__isnull=True))


class BulkActionMixin:
    """
    Adds a generic bulk-action form and the delete permission flag to the
    context of list views. Templates can then render the shared bulk toolbar.
    """

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)  # type: ignore
        model = getattr(self, "model", None)
        if model and hasattr(self, "object_list"):
            context["bulk_form"] = BulkActionForm()
            context["perms_delete_model"] = self.request.user.has_perm(
                "{}.delete_{}".format(model._meta.app_label, model._meta.model_name)
            )
        return context


def get_tenant_model_counts(group: Optional[Group]) -> int:
    """Helper function to count tenant items across all models for quota checking."""
    if not group:
        return 0

    from server.models import Model as Server
    from cluster.models import Model as Cluster
    from domain.models import Model as Domain
    from vendor.models import Model as Vendor
    from operatingsystem.models import Model as OS
    from status.models import Model as Status
    from location.models import Model as Location
    from patchtime.models import Model as Patchtime
    from servermodel.models import Model as ServerModel
    from clusterpackage.models import Model as ClusterPackage
    from clustersoftware.models import Model as ClusterSoftware
    from clusterpackagetype.models import Model as ClusterPackageType

    return (
        Server.objects.filter(group=group).count()
        + Cluster.objects.filter(group=group).count()
        + Domain.objects.filter(group=group).count()
        + Vendor.objects.filter(group=group).count()
        + OS.objects.filter(group=group).count()
        + Status.objects.filter(group=group).count()
        + Location.objects.filter(group=group).count()
        + Patchtime.objects.filter(group=group).count()
        + ServerModel.objects.filter(group=group).count()
        + ClusterPackage.objects.filter(group=group).count()
        + ClusterSoftware.objects.filter(group=group).count()
        + ClusterPackageType.objects.filter(group=group).count()
    )


class MultiTenantMixin:
    """
    Mixin to filter querysets by user groups and auto-assign group on save.
    Enforces item quotas per group.
    """

    def _tenant_permission_model(self) -> Any:
        """
        The model used for permission checks and history. Views whose queryset
        model differs from the app they belong to (e.g. grouped list views that
        return Vendor rows) may set ``permission_model`` to keep permission
        checks anchored to their own app.
        """
        return getattr(self, "permission_model", None) or getattr(self, "model", None)

    # Set on subclasses to block duplicate items within the same scope
    # (group, or the single global scope when group is null).
    unique_per_group_fields: tuple = ()

    def get_queryset(self) -> QuerySet:
        # Check basic view permission for the model
        model = self._tenant_permission_model()
        if model and not self.request.user.is_superuser:
            opts = model._meta
            codename = f"view_{opts.model_name.lower()}"
            if not self.request.user.has_perm(f"{opts.app_label}.{codename}"):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied

        queryset = super().get_queryset()  # type: ignore
        return filter_queryset_by_tenant(queryset, self.request)

    def dispatch(self, request, *args, **kwargs):
        """
        Server-side permission enforcement. Read requests require ``view``;
        write requests (POST) require ``add``/``change``/``delete`` for the
        relevant operation. Without this, template-only gating lets any
        view-only user POST directly to create/update/delete endpoints.
        """
        model = self._tenant_permission_model()
        if model and not request.user.is_superuser:
            opts = model._meta
            model_name = opts.model_name.lower()
            if request.method == "POST":
                action = required_permission_codename(self)
                perm = f"{opts.app_label}.{action}_{model_name}"
            else:
                perm = f"{opts.app_label}.view_{model_name}"
            if not request.user.has_perm(perm):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)  # type: ignore
        model = self._tenant_permission_model()
        # Only add history to context for ListViews that have it configured
        if model and hasattr(model, "history") and hasattr(self, "object_list"):
            history_qs = model.history.all()
            history_qs = filter_history_queryset_by_tenant(history_qs, self.request)
            context["recent_history"] = history_qs.order_by("-history_date")[:10]
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Only Create/Update views use SMForm-based forms that can scope FK
        # choices to a user; DeleteView's plain confirm form does not accept
        # a ``user`` kwarg.
        if required_permission_codename(self) in ("add", "change"):
            kwargs["user"] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        """
        Pre-assign the user's group to a new (unbound) form instance so the
        form's ``clean()`` can enforce per-group uniqueness before
        ``form_valid`` runs. This avoids SuccessMessageMixin emitting a false
        success message when the form is rejected.
        """
        form = super().get_form(form_class=form_class)  # type: ignore
        if not hasattr(form, "instance"):
            return form
        if (
            not form.instance.pk
            and not form.instance.group
            and not self.request.user.is_superuser
        ):
            user_groups = self.request.user.groups.all()
            if user_groups.exists():
                form.instance.group = user_groups.first()
        return form

    def check_quota(self, group: Optional[Group]) -> bool:
        if not group or not hasattr(group, "profile"):
            return True

        profile = group.profile
        max_items = profile.max_items

        # Count items across models with transaction to prevent race conditions
        with transaction.atomic():
            # Lock the group profile to prevent concurrent modifications
            GroupProfile = group.profile.__class__
            GroupProfile.objects.select_for_update().get(pk=profile.pk)

            count = get_tenant_model_counts(group)

            return count < max_items

    def form_valid(self, form: ModelForm) -> Any:
        # Delete confirm forms are plain ``Form``; resolve the target object
        # from the view for those, falling back to the bound model instance.
        instance = getattr(form, "instance", None)
        if instance is None:
            instance = getattr(self, "object", None)
        is_new = instance is None or not instance.pk

        # Global (group-less) seed fixtures are read-only reference data.
        # Tenant users must never be able to modify or delete them.
        if not is_new and not self.request.user.is_superuser:
            if getattr(instance, "group", None) is None:
                raise PermissionDenied
            # The group is immutable on update (editable=False); the form never
            # carries it, so nothing needs to be preserved here.
            return super().form_valid(form)  # type: ignore

        # New item: auto-assign the first group if not set and not superuser
        if is_new and not self.request.user.is_superuser:
            if instance is not None and not instance.group:
                user_groups = self.request.user.groups.all()
                if user_groups.exists():
                    instance.group = user_groups.first()
            # Users without a group may not create global rows
            if instance is None or getattr(instance, "group", None) is None:
                raise PermissionDenied

        # Check quota for NEW items
        if is_new:
            if not self.check_quota(getattr(instance, "group", None)):
                quota_limit = 0
                if instance and hasattr(instance, "group") and instance.group:
                    quota_limit = instance.group.profile.max_items
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
        # Check basic view permission for the model
        model = getattr(self, "model", None)
        if model and not self.request.user.is_superuser:
            opts = model._meta
            codename = f"view_{opts.model_name.lower()}"
            if not self.request.user.has_perm(f"{opts.app_label}.{codename}"):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied

        queryset = super().get_queryset()  # type: ignore
        return filter_queryset_by_tenant(queryset, self.request)

    def check_duplicate_per_group(
        self, serializer: Any, group: Optional[Group]
    ) -> None:
        """
        Rejects a create whose values collide with an existing item in the
        same scope. The scope is the target group, or the single global scope
        when the group is null. Because the DB UniqueConstraint(name, group)
        treats NULL rows as always-distinct, this guard is required to prevent
        duplicate *global* items (matching the web forms' behavior).

        Fields are derived from the model's ``UniqueConstraint`` declarations
        that include the ``group`` column, so it stays in sync with the DB.
        """
        model = getattr(serializer, "Meta", None)
        model = getattr(model, "model", None)
        if model is None:
            return
        from django.db.models import UniqueConstraint

        for constraint in model._meta.constraints:
            if not isinstance(constraint, UniqueConstraint):
                continue
            fields = list(constraint.fields)
            if "group" not in fields:
                continue
            fields.remove("group")
            if not fields:
                continue

            lookup = {}
            missing = False
            for field in fields:
                value = serializer.validated_data.get(field)
                # Nested related fields (e.g. SlugRelatedField) may be
                # serialized as the object itself or the pk.
                if hasattr(value, "pk"):
                    value = value.pk
                if value is None or value == "":
                    missing = True
                    break
                lookup[field] = value
            if missing:
                continue

            qs = model.objects.filter(**lookup)
            if group and group.pk:
                qs = qs.filter(group=group)
            else:
                qs = qs.filter(group__isnull=True)

            if qs.exists():
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    _("An item with these values already exists in this scope.")
                )

    def perform_create(self, serializer: Any) -> None:
        user_groups = self.request.user.groups.all()
        group = user_groups.first() if user_groups.exists() else None

        if not self.request.user.is_superuser:
            if group is None:
                raise DRFPermissionDenied(
                    _("You must belong to a group to create items.")
                )

            # Simple quota check for API with transaction
            if group and hasattr(group, "profile"):
                # Use transaction to ensure atomic count
                with transaction.atomic():
                    # Lock the group profile to prevent concurrent modifications
                    GroupProfile = group.profile.__class__
                    GroupProfile.objects.select_for_update().get(pk=group.profile.pk)

                    count = get_tenant_model_counts(group)
                if count >= group.profile.max_items:
                    raise ValidationError(_("Quota exceeded for this group."))

            # Block duplicates within the same scope (group or global).
            self.check_duplicate_per_group(serializer, group)

            serializer.save(group=group)
        else:
            serializer.save()

    def perform_update(self, serializer: Any) -> None:
        # Global (group-less) seed fixtures are read-only for tenant users
        if (
            not self.request.user.is_superuser
            and getattr(serializer.instance, "group", None) is None
        ):
            raise DRFPermissionDenied(
                _("Global reference data cannot be modified by tenant users.")
            )
        serializer.save()

    def perform_destroy(self, instance: Any) -> None:
        if (
            not self.request.user.is_superuser
            and getattr(instance, "group", None) is None
        ):
            raise DRFPermissionDenied(
                _("Global reference data cannot be deleted by tenant users.")
            )
        instance.delete()
