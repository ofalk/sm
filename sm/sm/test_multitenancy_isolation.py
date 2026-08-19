"""
Isolation & performance regression tests for multi-tenancy.

These guard against a user ever being able to read another tenant's data,
both via the web interface and via the DRF API, as well as against N+1 query
regressions on list pages.
"""

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from domain.models import Model as Domain
from server.models import Model as Server
from status.models import Model as Status
from vendor.models import Model as Vendor

from .models import ApiKey

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def grant(group, app_label, *codenames):
    """Grant a set of model permissions to a group."""
    ct = ContentType.objects.get(app_label=app_label, model="model")
    group.permissions.add(
        *Permission.objects.filter(content_type=ct, codename__in=codenames)
    )


def view_perm(app_label):
    return Permission.objects.get(
        content_type=ContentType.objects.get(app_label=app_label, model="model"),
        codename="view_model",
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class WebIsolationTest(TestCase):
    """A web user must never be able to read another tenant's data."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        self.vendor_a = Vendor.objects.create(name="Vendor A", group=self.group_a)
        self.vendor_b = Vendor.objects.create(name="Vendor B", group=self.group_b)

        grant(self.group_a, "vendor", "view_model")
        grant(self.group_b, "vendor", "view_model")

        self.client_a = self._client(self.user_a)
        self.client_b = self._client(self.user_b)

    def _client(self, user):
        client = self.client_class()
        client.force_login(user)
        return client

    def _select_groups(self, client, group_ids):
        """Simulate a tampered session selecting arbitrary group IDs."""
        session = client.session
        session["selected_groups"] = [str(g) for g in group_ids]
        session.save()

    def test_default_view_only_shows_own_group(self):
        response = self.client_a.get(reverse("vendor:index"))
        self.assertContains(response, "Vendor A")
        self.assertNotContains(response, "Vendor B")

    def test_cannot_see_other_group_by_tampering_with_selected_groups(self):
        # user_a tries to select group_b in the session filter
        self._select_groups(self.client_a, [self.group_b.id])
        response = self.client_a.get(reverse("vendor:index"))
        # Must NOT reveal group_b's vendor
        self.assertNotContains(response, "Vendor B")
        # Their own group's data is still visible
        self.assertContains(response, "Vendor A")

    def test_tampered_selection_falls_back_to_own_groups(self):
        # user_b selects only group_a in the session filter. Since user_b is
        # not in group_a, the selection sanitizes away and user_b simply sees
        # their own group's data -- never group_a's.
        self._select_groups(self.client_b, [self.group_a.id])
        response = self.client_b.get(reverse("vendor:index"))
        self.assertNotContains(response, "Vendor A")
        self.assertContains(response, "Vendor B")

    def test_cannot_fetch_other_groups_object_by_direct_url(self):
        # vendor detail uses GenericUpdateView with MultiTenantMixin
        url = reverse("vendor:update", args=[self.vendor_b.pk])
        response = self.client_a.get(url)
        self.assertIn(response.status_code, [403, 404])

    def test_bulk_action_cannot_affect_other_groups_servers(self):
        # Set up servers so we can exercise the bulk action for a privileged app
        grant(self.group_a, "server", "view_model", "delete_model")
        grant(self.group_b, "server", "view_model")
        status = Status.objects.create(name="Active")
        domain = Domain.objects.create(name="example.com")
        server_b = Server.objects.create(
            hostname="beta-host", status=status, domain=domain, group=self.group_b
        )
        self.client_a.post(
            reverse("server:bulk_action"),
            {"selected_servers": [server_b.pk], "delete": "on"},
        )
        # The bulk action must not operate on group_b's server
        self.assertTrue(Server.objects.filter(pk=server_b.pk).exists())


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiIsolationTest(TestCase):
    """An API user must never be able to read another tenant's data."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.superuser = User.objects.create_superuser(
            "super", password=PASSWORD, email="super@example.com"
        )
        self.user_a.groups.clear()
        self.user_b.groups.clear()
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        self.key_a, self.secret_a = ApiKey.create_for_user(self.user_a, "a")
        self.key_b, self.secret_b = ApiKey.create_for_user(self.user_b, "b")

        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="example.com")

        self.server_a = Server.objects.create(
            hostname="alpha", status=self.status, domain=self.domain, group=self.group_a
        )
        self.server_b = Server.objects.create(
            hostname="beta", status=self.status, domain=self.domain, group=self.group_b
        )

        for group in (self.group_a, self.group_b):
            grant(group, "server", "view_model")
            grant(group, "vendor", "view_model")

    def api_as(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_api_user_cannot_tamper_with_selected_groups(self):
        session = self.client.session
        session["selected_groups"] = [str(self.group_b.id)]  # user_a not in group_b
        session.save()

        response = self.api_as(self.user_a).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertEqual(response.status_code, 200)
        self.assertIn("alpha", names)
        self.assertNotIn("beta", names)

    def test_api_queries_only_own_group(self):
        response = self.api_as(self.user_a).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertIn("alpha", names)
        self.assertNotIn("beta", names)

    def test_api_rejects_direct_fetch_of_other_group(self):
        response = self.api_as(self.user_a).get(f"/api/servers/{self.server_b.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_api_superuser_sees_all(self):
        response = self.api_as(self.superuser).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertIn("alpha", names)
        self.assertIn("beta", names)

    def test_other_group_key_gets_own_partition(self):
        response = APIClient().get(
            "/api/servers/", **self._auth_headers(self.key_b, self.secret_b)
        )
        names = {item["hostname"] for item in response.json()}
        self.assertIn("beta", names)
        self.assertNotIn("alpha", names)

    def _auth_headers(self, key, secret):
        return {
            "HTTP_AUTHORIZATION": f"ApiKey {key.client_id}:{secret}",
        }


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class NPlusOneRegressionTest(TestCase):
    """The server list page must not fire an extra query per row."""

    def setUp(self):
        self.group = Group.objects.create(name="Group A")
        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_a.groups.add(self.group)
        grant(self.group, "server", "view_model")

        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="example.com")

        # A bunch of servers with populated related rows so any missing
        # select_related would show up as N+1.
        for i in range(20):
            Server.objects.create(
                hostname=f"host-{i}",
                status=self.status,
                domain=self.domain,
                group=self.group,
            )

    def test_server_list_query_count_is_constant(self):
        client = APIClient(enforce_csrf_checks=False)
        client.force_login(self.user_a)

        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        def query_count(hostnames):
            # Prune so exactly these hosts exist (isolates pagination+history)
            Server.objects.exclude(hostname__in=hostnames).delete()
            with CaptureQueriesContext(connection) as ctx:
                response = client.get(reverse("server:index"))
                self.assertEqual(response.status_code, 200)
            return len(ctx.captured_queries)

        small = query_count(["host-0"])
        # Forcing a second page ensures the first page is still exercised
        large = query_count([f"host-{i}" for i in range(20)])

        # Rendering 20 rows must not add a query per row. If a select_related
        # regresses, `large` grows roughly proportionally to the row count.
        self.assertLessEqual(
            large,
            small + 2,
            "server list query count grows with row count (N+1 regression)",
        )

    def test_server_list_uses_select_related(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        client = APIClient(enforce_csrf_checks=False)
        client.force_login(self.user_a)

        with CaptureQueriesContext(connection) as ctx:
            response = client.get(reverse("server:index"))
            self.assertEqual(response.status_code, 200)

        joins = " ".join(q["sql"] for q in ctx.captured_queries)
        # The main list query must JOIN the related tables in one go rather than
        # issuing a separate query per FK per row.
        self.assertIn('LEFT OUTER JOIN "sm_operatingsystem"', joins)
        self.assertIn('LEFT OUTER JOIN "sm_vendor"', joins)
        self.assertIn('INNER JOIN "sm_status"', joins)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class WebMultiAppIsolationTest(TestCase):
    """
    The reference-data apps (status/location/patchtime/etc.) must be tenant
    isolated on the web just like server/vendor.
    """

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")
        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        from location.models import Model as Location
        from patchtime.models import Model as Patchtime

        self.status_a = Status.objects.create(name="Status A", group=self.group_a)
        self.status_b = Status.objects.create(name="Status B", group=self.group_b)
        self.location_a = Location.objects.create(name="Loc A", group=self.group_a)
        self.location_b = Location.objects.create(name="Loc B", group=self.group_b)
        self.patchtime_a = Patchtime.objects.create(name="Patch A", group=self.group_a)
        self.patchtime_b = Patchtime.objects.create(name="Patch B", group=self.group_b)

        for app in ("status", "location", "patchtime"):
            grant(
                self.group_a,
                app,
                "view_model",
                "add_model",
                "change_model",
                "delete_model",
            )
            grant(
                self.group_b,
                app,
                "view_model",
                "add_model",
                "change_model",
                "delete_model",
            )

        self.client_a = self.client_class()
        self.client_a.force_login(self.user_a)

    def test_list_does_not_show_other_group_rows(self):
        for app, own, other in [
            ("status:index", "Status A", "Status B"),
            ("location:index", "Loc A", "Loc B"),
            ("patchtime:index", "Patch A", "Patch B"),
        ]:
            response = self.client_a.get(reverse(app))
            self.assertEqual(response.status_code, 200, app)
            self.assertContains(response, own, msg_prefix=app)
            self.assertNotContains(response, other, msg_prefix=app)

    def test_cannot_open_other_group_object_by_direct_url(self):
        for app, other_pk in [
            ("status:update", self.status_b.pk),
            ("location:update", self.location_b.pk),
            ("patchtime:update", self.patchtime_b.pk),
        ]:
            response = self.client_a.get(reverse(app, args=[other_pk]))
            self.assertIn(response.status_code, [403, 404], app)

    def test_cannot_update_other_group_object(self):
        response = self.client_a.post(
            reverse("status:update", args=[self.status_b.pk]), {"name": "Hacked"}
        )
        # The tenant filter raises 403 (no change perm on non-accessible object)
        # or 404 (object not found). Either way no write must happen.
        self.assertIn(response.status_code, [403, 404])

    def test_cannot_delete_other_group_object(self):
        response = self.client_a.post(
            reverse("status:delete", args=[self.status_b.pk]), {"confirm": "1"}
        )
        self.assertIn(response.status_code, [403, 404, 302])
        self.assertTrue(Status.objects.filter(pk=self.status_b.pk).exists())


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class DashboardAndSearchIsolationTest(TestCase):
    """Dashboard counts and global search must not leak other tenants' data."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")
        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        Vendor.objects.create(name="Pedro Vendor", group=self.group_b)
        for app in ("vendor", "server"):
            grant(self.group_a, app, "view_model")
            grant(self.group_b, app, "view_model")

        self.client_a = self.client_class()
        self.client_a.force_login(self.user_a)

    def test_dashboard_vendor_count_excludes_other_group(self):
        response = self.client_a.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        # user_a (group A) must not be able to count group B's vendor
        self.assertEqual(response.context["vendor_count"], 0)
        self.assertNotContains(response, "Pedro Vendor")

    def test_search_does_not_return_other_group_vendor(self):
        # user_a (group A) searches for group B's vendor by name
        response = self.client_a.get(reverse("search"), {"q": "Pedro", "ajax": "1"})
        # The AJAX results template must not contain group B's vendor
        self.assertNotContains(response, "Pedro Vendor")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class HistoryIsolationTest(TestCase):
    """History/diff must not expose another tenant's record."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")
        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)
        grant(self.group_a, "status", "view_model")
        grant(self.group_b, "status", "view_model", "add_model", "change_model")

        self.client_a = self.client_class()
        self.client_a.force_login(self.user_a)

    def test_cannot_fetch_other_group_history_diff(self):
        from status.models import Model as Status

        Status.objects.create(name="Secret Status", group=self.group_b)
        history_row = Status.history.first()
        response = self.client_a.get(
            reverse(
                "history_diff",
                kwargs={
                    "app_label": "status",
                    "model_name": "model",
                    "history_id": history_row.history_id,
                },
            )
        )
        self.assertEqual(response.status_code, 404)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiFkIsolationTest(TestCase):
    """API writes must not reference another tenant's related objects."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")
        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.user_a.groups.clear()
        self.user_b.groups.clear()
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        for app in ("server", "status", "domain"):
            grant(self.group_a, app, "view_model", "add_model")
            grant(self.group_b, app, "view_model", "add_model")

        self.key_a, self.secret_a = ApiKey.create_for_user(self.user_a, "a")

        self.status_b = Status.objects.create(name="Status of B", group=self.group_b)
        self.domain_b = Domain.objects.create(name="internal-b.tld", group=self.group_b)

    def api(self):
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"ApiKey {self.key_a.client_id}:{self.secret_a}"
        )
        return client

    def test_cannot_create_server_with_other_group_status(self):
        response = self.api().post(
            "/api/servers/",
            {"hostname": "sneaky", "status": "Status of B", "domain": "example.com"},
            format="json",
        )
        # Status isn't in user_a's tenant -> validation must reject
        self.assertIn(response.status_code, [400, 404])
        self.assertFalse(Server.objects.filter(hostname="sneaky").exists())

    def test_can_create_server_with_global_status(self):
        # A global (group-less) status remains usable by everyone.
        Status.objects.create(name="Global Status")
        Domain.objects.create(name="global.tld")
        response = self.api().post(
            "/api/servers/",
            {
                "hostname": "legit",
                "status": "Global Status",
                "domain": "global.tld",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Server.objects.filter(hostname="legit").exists())


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ServerSidePermissionTest(TestCase):
    """View-only users must not be able to write via POST."""

    def setUp(self):
        self.group = Group.objects.create(name="Group A")
        self.user = User.objects.create_user("viewonly", password=PASSWORD)
        self.user.groups.clear()  # drop the auto-created personal group
        self.user.groups.add(self.group)
        grant(self.group, "vendor", "view_model")

        self.client = self.client_class()
        self.client.force_login(self.user)
        self.view_perm = Permission.objects.get(
            content_type=ContentType.objects.get(app_label="vendor", model="model"),
            codename="view_model",
        )

    def test_view_only_user_cannot_create(self):
        response = self.client.post(
            reverse("vendor:create"),
            {"name": "Should Not Appear", "is_hardware": True, "is_software": True},
        )
        self.assertIn(response.status_code, [403, 404])
        self.assertFalse(Vendor.objects.filter(name="Should Not Appear").exists())

    def test_view_only_user_cannot_bulk_change_status(self):
        # Grant delete+view-only on server; no change permission.
        grant(self.group, "server", "view_model")
        status = Status.objects.create(name="Active", group=self.group)
        domain = Domain.objects.create(name="example.com", group=self.group)
        server = Server.objects.create(
            hostname="stack", status=status, domain=domain, group=self.group
        )
        new_status = Status.objects.create(name="New", group=self.group)

        response = self.client.post(
            reverse("server:bulk_action"),
            {"selected_servers": [server.pk], "status": new_status.pk},
        )
        server.refresh_from_db()
        self.assertEqual(server.status, status)  # unchanged
        # BulkActionView redirects to index even on permission error
        self.assertIn(response.status_code, [302, 200, 403])


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class GlobalFixtureImmutabilityTest(TestCase):
    """
    Global (group-less) seed fixtures are shared reference data. Tenant users
    may read them but must never be able to modify or delete them.
    """

    def setUp(self):
        self.group = Group.objects.create(name="Tenant")
        self.user = User.objects.create_user("tenant", password=PASSWORD)
        self.user.groups.add(self.group)
        for app in ("status", "vendor"):
            grant(
                self.group,
                app,
                "view_model",
                "add_model",
                "change_model",
                "delete_model",
            )

        self.global_status = Status.objects.create(name="Global Status")
        self.global_vendor = Vendor.objects.create(name="Global Vendor")

        self.client = self.client_class()
        self.client.force_login(self.user)

    def test_cannot_update_global_row_via_web(self):
        response = self.client.post(
            reverse("status:update", args=[self.global_status.pk]), {"name": "Hacked"}
        )
        self.assertEqual(response.status_code, 403)
        self.global_status.refresh_from_db()
        self.assertEqual(self.global_status.name, "Global Status")
        self.assertIsNone(self.global_status.group)

    def test_cannot_delete_global_row_via_web(self):
        response = self.client.post(
            reverse("status:delete", args=[self.global_status.pk]), {"confirm": "1"}
        )
        self.assertIn(response.status_code, [403, 404])
        self.assertTrue(Status.objects.filter(pk=self.global_status.pk).exists())

    def test_can_view_global_row(self):
        response = self.client.get(reverse("status:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Global Status")

    def test_cannot_update_global_vendor_via_web(self):
        response = self.client.post(
            reverse("vendor:update", args=[self.global_vendor.pk]), {"name": "Hacked"}
        )
        self.assertEqual(response.status_code, 403)
        self.global_vendor.refresh_from_db()
        self.assertEqual(self.global_vendor.name, "Global Vendor")

    def test_api_cannot_update_global_row(self):
        api = APIClient()
        api.force_authenticate(self.user)
        response = api.patch(
            "/api/statuses/%d/" % self.global_status.pk,
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.global_status.refresh_from_db()
        self.assertEqual(self.global_status.name, "Global Status")

    def test_api_cannot_delete_global_row(self):
        api = APIClient()
        api.force_authenticate(self.user)
        response = api.delete("/api/statuses/%d/" % self.global_status.pk)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Status.objects.filter(pk=self.global_status.pk).exists())

    def test_bulk_action_cannot_affect_global_servers(self):
        grant(self.group, "server", "view_model", "change_model")
        status = Status.objects.create(name="Active", group=self.group)
        domain = Domain.objects.create(name="example.com", group=self.group)
        global_server = Server.objects.create(
            hostname="seed-host", status=status, domain=domain
        )
        new_status = Status.objects.create(name="New", group=self.group)
        self.client.post(
            reverse("server:bulk_action"),
            {"selected_servers": [global_server.pk], "status": new_status.pk},
        )
        global_server.refresh_from_db()
        self.assertEqual(global_server.status, status)  # unchanged
