from django.db import models
from django.contrib.auth.models import Group, User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from typing import Any
import uuid


class GroupProfile(models.Model):
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="profile"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_groups",
    )
    max_items = models.PositiveIntegerField(
        default=200,
        help_text="Maximum number of items across all models for this group.",
    )
    max_users = models.PositiveIntegerField(
        default=2, help_text="Maximum number of users allowed in this group."
    )

    def __str__(self) -> str:
        return f"Profile for {self.group.name}"

    class Meta:
        verbose_name = "Group Profile"
        verbose_name_plural = "Group Profiles"


@receiver(post_save, sender=Group)
def create_group_profile(
    sender: Any, instance: Group, created: bool, **kwargs: Any
) -> None:
    if created:
        GroupProfile.objects.get_or_create(group=instance)
        from .utils_permissions import sync_group_permissions

        # Default to view-only, GroupCreateView will upgrade this if needed
        sync_group_permissions(instance, grant_all=False)


@receiver(post_save, sender=User)
def create_personal_group(
    sender: Any, instance: User, created: bool, **kwargs: Any
) -> None:
    """
    Ensures every new user has their own personal group to start with.
    """
    if created:
        group_name = f"{instance.username}'s Workspace"
        # Ensure name uniqueness
        if Group.objects.filter(name=group_name).exists():
            group_name = f"{instance.username}'s Workspace ({uuid.uuid4().hex[:4]})"

        group = Group.objects.create(name=group_name)
        # Profile is already created by create_group_profile signal
        profile = group.profile
        profile.owner = instance
        profile.save()

        instance.groups.add(group)

        # Grant full permissions for personal workspace
        from .utils_permissions import sync_group_permissions

        sync_group_permissions(group, grant_all=True)


class Invitation(models.Model):
    email = models.EmailField()
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="invitations"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="invitations_sent"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        unique_together = ["email", "group"]

    def __str__(self) -> str:
        return f"Invitation for {self.email} to {self.group.name}"

    def is_expired(self) -> bool:
        return timezone.now() - self.created_at > timezone.timedelta(hours=24)
