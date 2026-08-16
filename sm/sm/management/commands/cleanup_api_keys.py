from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from sm.models import ApiKey


class Command(BaseCommand):
    help = (
        "Revoke API keys that have expired or have been inactive for too long. "
        "Use --inactive-days to control the inactivity threshold (default 90)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--inactive-days",
            type=int,
            default=90,
            help="Revoke keys unused for this many days (default: 90).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be revoked without changing anything.",
        )

    def handle(self, *args, **options):
        inactive_days = options["inactive_days"]
        dry_run = options["dry_run"]
        now = timezone.now()

        expired = ApiKey.objects.filter(
            is_active=True, expires_at__isnull=False, expires_at__lte=now
        )
        inactive = ApiKey.objects.filter(
            is_active=True,
            expires_at__isnull=True,
            last_used_at__isnull=False,
            last_used_at__lte=now - timedelta(days=inactive_days),
        )

        expired_count = expired.count()
        inactive_count = inactive.count()
        self.stdout.write(
            self.style.WARNING(
                "Found %d expired and %d inactive API key(s)."
                % (expired_count, inactive_count)
            )
        )

        if dry_run:
            self.stdout.write("Dry run - nothing was revoked.")
            return

        for key in expired:
            key.is_active = False
            key.revoked_at = now
            key.save(update_fields=["is_active", "revoked_at"])
        for key in inactive:
            key.is_active = False
            key.revoked_at = now
            key.save(update_fields=["is_active", "revoked_at"])

        self.stdout.write(
            self.style.SUCCESS(
                "Revoked %d expired and %d inactive API key(s)."
                % (expired_count, inactive_count)
            )
        )
