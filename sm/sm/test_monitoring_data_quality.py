from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from clusterpackagetype.models import Model as ClusterPackageType
from clustersoftware.models import Model as ClusterSoftware
from domain.models import Model as Domain
from server.models import Model as Server
from status.models import Model as Status
from vendor.models import Model as Vendor


class MonitoringDataQualityCommandTest(TestCase):
    def setUp(self):
        self.status_in_use = Status.objects.create(name="In use")
        self.status_other = Status.objects.create(name="Planned")
        self.domain = Domain.objects.create(name="localghost.com")
        self.server = Server.objects.create(
            hostname="knode03",
            domain=self.domain,
            status=self.status_in_use,
            monitoring_from_puppet=False,
        )
        vendor = Vendor.objects.create(name="AlmaLinux")
        software = ClusterSoftware.objects.create(
            name="PostgreSQL", version="17", vendor=vendor
        )
        self.cluster = Cluster.objects.create(
            name="k.localghost.com", clustersoftware=software
        )
        self.package = ClusterPackage.objects.create(
            name="central-postgres-rw",
            cluster=self.cluster,
            package_type=ClusterPackageType.objects.create(name="PostgreSQL R/W"),
            status=self.status_other,
            host="10.0.0.2",
            monitoring=True,
        )

    def test_dry_run_reports_without_changing_data(self):
        out = StringIO()
        call_command("monitoring_data_quality", stdout=out)

        self.server.refresh_from_db()
        self.package.refresh_from_db()
        self.assertFalse(self.server.monitoring_from_puppet)
        self.assertEqual(self.package.status, self.status_other)
        self.assertIn("Dry run", out.getvalue())

    def test_apply_normalises_server_and_package(self):
        out = StringIO()
        call_command("monitoring_data_quality", "--apply", stdout=out)

        self.server.refresh_from_db()
        self.package.refresh_from_db()
        self.assertTrue(self.server.monitoring_from_puppet)
        self.assertEqual(self.package.status, self.status_in_use)
        self.assertIn("Marked 1 active server(s) as monitored", out.getvalue())
        self.assertIn("Moved 1 monitored package(s)", out.getvalue())

    def test_skip_status_option(self):
        out = StringIO()
        call_command("monitoring_data_quality", "--apply", "--skip-status", stdout=out)

        self.server.refresh_from_db()
        self.package.refresh_from_db()
        self.assertTrue(self.server.monitoring_from_puppet)
        self.assertEqual(self.package.status, self.status_other)
        self.assertIn("Skipped cluster package status", out.getvalue())

    def test_reports_duplicate_fqdn(self):
        Server.objects.create(
            hostname="knode03",
            domain=self.domain,
            status=self.status_in_use,
        )
        out = StringIO()
        call_command("monitoring_data_quality", stdout=out)
        self.assertIn("Duplicate FQDNs", out.getvalue())
        self.assertIn("knode03.localghost.com", out.getvalue())
