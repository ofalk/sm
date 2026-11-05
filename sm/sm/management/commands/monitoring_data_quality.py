from django.core.management.base import BaseCommand
from django.db.models import Count

from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from server.models import Model as Server
from status.models import Model as Status


class Command(BaseCommand):
    """
    Audit the data required by the monitoring coverage exporter.

    Without ``--apply`` the command only reports. With ``--apply`` it makes the
    two safe, explicitly requested corrections:

    * mark active ``In use`` servers as monitored;
    * move monitored cluster packages to their scope's ``In use`` status.

    Duplicate FQDNs are reported but never changed automatically: resolving
    them is a tenancy decision.
    """

    help = (
        "Report monitoring data quality, and optionally normalise active server "
        "monitoring flags and monitored package statuses."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the safe normalisations instead of only reporting.",
        )
        parser.add_argument(
            "--skip-status",
            action="store_true",
            help="Do not change cluster package statuses (only report them).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        skip_status = options["skip_status"]

        active_servers = Server.objects.filter(
            status__name="In use", decommission_date__isnull=True
        )
        unmonitored_active = active_servers.filter(monitoring_from_puppet=False)

        duplicates = (
            Server.objects.values("hostname", "domain__name")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("hostname")
        )

        monitored_packages = ClusterPackage.objects.filter(monitoring=True)
        wrong_status_packages = monitored_packages.exclude(status__name="In use")

        self.stdout.write("Monitoring data quality")
        self.stdout.write("=======================")
        self.stdout.write(
            "Active 'In use' servers: %d (unmonitored: %d)"
            % (active_servers.count(), unmonitored_active.count())
        )
        self.stdout.write(
            "Clusters not monitored: %d"
            % Cluster.objects.filter(monitoring=False).count()
        )
        self.stdout.write(
            "Cluster packages not monitored: %d"
            % ClusterPackage.objects.filter(monitoring=False).count()
        )
        self.stdout.write(
            "Monitored packages not in 'In use': %d" % wrong_status_packages.count()
        )

        if duplicates:
            self.stdout.write(
                self.style.WARNING(
                    "Duplicate FQDNs across groups (resolve manually): %d"
                    % duplicates.count()
                )
            )
            for row in duplicates:
                self.stdout.write(
                    "  - %s.%s (%d servers)"
                    % (row["hostname"], row["domain__name"], row["total"])
                )
        else:
            self.stdout.write("Duplicate FQDNs: none")

        self.stdout.write(
            "API visibility: use a key owned by a superuser (or a user in every "
            "group) so the exporter can read all tenants."
        )

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run - nothing changed. Re-run with --apply to update "
                    "server flags and package statuses."
                )
            )
            return

        updated_servers = unmonitored_active.update(monitoring_from_puppet=True)
        self.stdout.write(
            self.style.SUCCESS(
                "Marked %d active server(s) as monitored." % updated_servers
            )
        )

        if skip_status:
            self.stdout.write("Skipped cluster package status changes.")
            return

        updated_packages = 0
        skipped_packages = 0
        for package in wrong_status_packages.select_related("group"):
            status_qs = Status.objects.filter(name="In use")
            status = None
            if package.group_id:
                status = status_qs.filter(group_id=package.group_id).first()
            if status is None:
                status = status_qs.filter(group__isnull=True).first()
            if status is None:
                skipped_packages += 1
                continue
            package.status = status
            package.save(update_fields=["status"])
            updated_packages += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Moved %d monitored package(s) to 'In use' (skipped: %d, no "
                "scope status found)." % (updated_packages, skipped_packages)
            )
        )
