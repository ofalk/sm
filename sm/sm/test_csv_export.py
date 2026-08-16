import csv
import io

from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def grant(group, app, *codenames):
    ct = ContentType.objects.get(app_label=app, model="model")
    group.permissions.add(
        *Permission.objects.filter(content_type=ct, codename__in=codenames)
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class CSVExportTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Export Group")
        self.superuser = User.objects.create_superuser("exporter", "e@e.c", PASSWORD)
        self.client.force_login(self.superuser)
        from vendor.models import Model as Vendor
        from status.models import Model as Status
        from domain.models import Model as Domain
        from server.models import Model as Server

        self.vendor = Vendor.objects.create(name="CSV Vendor")
        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="csv.example.com")
        self.server = Server.objects.create(
            hostname="csvhost01",
            status=self.status,
            domain=self.domain,
            application="App",
            rack="R-1",
        )

    def _read_csv(self, response):
        return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))

    def test_vendor_export(self):
        response = self.client.get(reverse("vendor:export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = self._read_csv(response)
        self.assertEqual(rows[0], ["name", "is_hardware", "is_software"])
        self.assertTrue(any("CSV Vendor" in row for row in rows))

    def test_server_export_includes_new_fields(self):
        response = self.client.get(reverse("server:export"))
        rows = self._read_csv(response)
        self.assertEqual(rows[0][0], "hostname")
        header = rows[0]
        self.assertIn("application", header)
        self.assertIn("rack", header)
        server_row = next(r for r in rows if r and r[0] == "csvhost01")
        self.assertIn("App", server_row)
        self.assertIn("R-1", server_row)

    def test_domain_export(self):
        response = self.client.get(reverse("domain:export"))
        rows = self._read_csv(response)
        self.assertEqual(rows[0], ["name"])
        self.assertTrue(any("csv.example.com" in row for row in rows))

    def test_export_respects_tenancy(self):
        other = Group.objects.create(name="Other Export Group")
        from vendor.models import Model as Vendor

        Vendor.objects.create(name="Secret Vendor", group=other)
        user = User.objects.create_user("exportuser", password=PASSWORD)
        user.groups.add(self.group)
        grant(self.group, "vendor", "view_model")
        self.client.logout()
        self.client.force_login(user)

        response = self.client.get(reverse("vendor:export"))
        rows = self._read_csv(response)
        names = {row[0] for row in rows[1:]}
        self.assertNotIn("Secret Vendor", names)
        self.assertIn("CSV Vendor", names)

    def test_export_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("vendor:export"))
        self.assertEqual(response.status_code, 302)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class CSVExportButtonTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("btnexporter", "e@e.c", PASSWORD)
        self.client.force_login(self.superuser)

    def test_list_pages_have_export_button(self):
        for app in [
            "server",
            "cluster",
            "domain",
            "vendor",
            "location",
            "operatingsystem",
            "servermodel",
            "status",
            "patchtime",
            "clustersoftware",
            "clusterpackagetype",
            "clusterpackage",
        ]:
            response = self.client.get(reverse(f"{app}:index"))
            self.assertEqual(response.status_code, 200, f"{app}:index")
            self.assertContains(
                response, "file-csv", msg_prefix=f"{app} list missing export"
            )
