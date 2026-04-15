from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def get_group_permissions_for_model(
    app_label: str, model_name: str = "model"
) -> List[Permission]:
    """
    Returns the standard permissions (view, add, change, delete) for a model.
    """
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        return list(Permission.objects.filter(content_type=ct))
    except ContentType.DoesNotExist:
        logger.warning(f"ContentType for {app_label}.{model_name} not found.")
        return []


def assign_group_permissions(group: Group, permissions: List[Permission]) -> None:
    """
    Assigns a list of permissions to a group.
    """
    group.permissions.add(*permissions)


def sync_group_permissions(group: Group, grant_all: bool = False) -> None:
    """
    Ensures a group has at least basic view permissions for the core models
    so multi-tenancy works as expected.
    If grant_all is True, also grants add, change, and delete permissions.
    """
    app_models: List[Tuple[str, str]] = [
        ("server", "model"),
        ("cluster", "model"),
        ("domain", "model"),
        ("vendor", "model"),
        ("operatingsystem", "model"),
        ("status", "model"),
        ("location", "model"),
        ("patchtime", "model"),
        ("servermodel", "model"),
        ("clusterpackage", "model"),
        ("clustersoftware", "model"),
        ("clusterpackagetype", "model"),
    ]

    for app, model in app_models:
        perms = get_group_permissions_for_model(app, model)
        if grant_all:
            # Grant all permissions for this model
            group.permissions.add(*perms)
        else:
            # By default, give view permission to every group
            view_perm = next((p for p in perms if p.codename.startswith("view_")), None)
            if view_perm:
                group.permissions.add(view_perm)
            else:
                logger.debug(f"View permission for {app}.{model} not found.")
