"""Regression tests for the tenant-isolation and XSS audit findings.

These exercise the paths that duplicated (and previously bypassed) the shared
tenant filter, plus the dashboard chart labels that were rendered with
``|safe`` inside an inline ``<script>``.
"""

import csv
import io

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from domain.models import Model as Domain
from server.models import Model as Server
from status.models import Model as Status
from vendor.models import Model as Vendor

from .test_multitenancy_isolation import FAST_HASHERS, PASSWORD, grant


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SelectedGroupTamperingTest(TestCase):
    """A tampered session selection must never cross tenant boundaries."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Tenant A")
        self.group_b = Group.objects.create(name="Tenant B")

        self.user = User.objects.create_user("tenantuser", password=PASSWORD)
        self.user.groups.add(self.group_a)
        grant(self.group_a, "vendor", "view_model", "delete_model")

        self.vendor_a = Vendor.objects.create(name="Vendor A", group=self.group_a)
        self.vendor_b = Vendor.objects.create(name="Vendor B", group=self.group_b)

        self.client.force_login(self.user)

    def _tamper_session(self):
        session = self.client.session
        session["selected_groups"] = [str(self.group_b.pk)]
        session.save()

    def test_group_filter_drops_foreign_ids(self):
        self.client.post(reverse("group_filter"), {"groups": str(self.group_b.pk)})
        self.assertNotIn(str(self.group_b.pk), self.client.session["selected_groups"])

    def test_export_does_not_leak_foreign_group(self):
        self._tamper_session()
        response = self.client.get(reverse("vendor:export"))
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Vendor A", body)
        self.assertNotIn("Vendor B", body)

    def test_bulk_delete_cannot_delete_foreign_group(self):
        self._tamper_session()
        self.client.post(
            reverse("vendor:bulk_delete"), {"selected_ids": [self.vendor_b.pk]}
        )
        self.assertTrue(Vendor.objects.filter(pk=self.vendor_b.pk).exists())

    def test_patch_schedule_does_not_leak_foreign_group(self):
        status = Status.objects.create(name="Active")
        domain = Domain.objects.create(name="example.com")
        Server.objects.create(
            hostname="secret-host-b",
            status=status,
            domain=domain,
            group=self.group_b,
        )
        self._tamper_session()
        response = self.client.get(reverse("patch_schedule"))
        self.assertNotContains(response, "secret-host-b")

    def test_export_requires_view_permission(self):
        without_perms = User.objects.create_user("noperm", password=PASSWORD)
        # New users get an auto-provisioned workspace group; strip all
        # permissions so this user truly has none.
        for group in without_perms.groups.all():
            group.permissions.clear()
        without_perms.user_permissions.clear()
        self.client.force_login(without_perms)
        response = self.client.get(reverse("vendor:export"))
        self.assertEqual(response.status_code, 403)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class CsvFormulaInjectionTest(TestCase):
    """Exported cells must not be interpreted as spreadsheet formulas."""

    def test_formula_cells_are_prefixed(self):
        admin = User.objects.create_superuser("csvadmin", password=PASSWORD)
        Vendor.objects.create(name="=cmd|' /C calc'!A0")
        self.client.force_login(admin)

        response = self.client.get(reverse("vendor:export"))
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertTrue(rows[1][0].startswith("'="))


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class DashboardChartXssTest(TestCase):
    """User-controlled chart labels must not break out of the script block."""

    PAYLOAD = "</script><script>alert(1)</script>"

    def test_status_label_is_escaped_in_inline_script(self):
        admin = User.objects.create_superuser("xssadmin", password=PASSWORD)
        self.client.force_login(admin)

        status = Status.objects.create(name=self.PAYLOAD)
        domain = Domain.objects.create(name="xss.example.com")
        Server.objects.create(hostname="xss-host", status=status, domain=domain)

        response = self.client.get(reverse("dashboard"))
        body = response.content.decode()
        self.assertNotIn(self.PAYLOAD, body)
        self.assertIn("\\u003c/script\\u003e", body)
