from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from server.models import Model as Server


def _notification_enabled() -> bool:
    return getattr(settings, "SERVER_STATUS_NOTIFY", False)


def _recipients(server: Server) -> list:
    """Group members with an email address, plus superusers."""
    users = set()
    if server.group_id:
        for user in server.group.user_set.all():
            if user.email:
                users.add(user.email)
    for user in get_user_model().objects.filter(is_superuser=True):
        if user.email:
            users.add(user.email)
    return sorted(users)


def _send_status_change_email(instance: Server) -> None:
    recipients = _recipients(instance)
    if not recipients:
        return

    subject = _("Server %(hostname)s status changed to %(status)s") % {
        "hostname": instance.hostname,
        "status": instance.status.name if instance.status_id else _("unknown"),
    }
    message = render_to_string(
        "notifications/server_status_change.txt",
        {
            "server": instance,
            "status": instance.status,
            "group": instance.group,
        },
    )
    send_mail(
        subject,
        message,
        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@servermanager"),
        recipients,
        fail_silently=True,
    )


@receiver(pre_save, sender=Server)
def remember_status_change(sender, instance, **kwargs):
    """Capture the previous status so we can detect changes in post_save."""
    if instance.pk is None:
        instance._old_status_id = None
        return
    try:
        old = Server.objects.filter(pk=instance.pk).values("status_id").first()
        instance._old_status_id = old["status_id"] if old else None
    except Server.DoesNotExist:
        instance._old_status_id = None


@receiver(post_save, sender=Server)
def notify_on_status_change(sender, instance, created, **kwargs):
    """Send an email to the server's group members when its status changes."""
    if created or not _notification_enabled():
        return
    old_status_id = getattr(instance, "_old_status_id", None)
    if old_status_id == instance.status_id:
        return
    _send_status_change_email(instance)
