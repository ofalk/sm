from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ServerLifecycleTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("lifecycle", "l@e.c", PASSWORD)
        self.client.force_login(self.superuser)

        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        self.status = Status.objects.create(name="In use")
        self.domain = Domain.objects.create(name="lifecycle.example.com")
        self.server = Server.objects.create(
            hostname="lifecycle01", status=self.status, domain=self.domain
        )

    def test_default_lifecycle_is_active(self):
        self.assertIsNone(self.server.decommission_date)
        self.assertFalse(self.server.is_decommissioned)
        self.assertIn(self.server.lifecycle_stage, ("ordered", "installed"))

    def test_decommission_sets_date(self):
        response = self.client.post(
            reverse("server:decommission", args=[self.server.pk])
        )
        self.assertRedirects(response, reverse("server:index"))
        self.server.refresh_from_db()
        self.assertIsNotNone(self.server.decommission_date)
        self.assertEqual(self.server.decommission_date, timezone.localdate())
        self.assertTrue(self.server.is_decommissioned)
        self.assertEqual(self.server.lifecycle_stage, "decommissioned")

    def test_restore_clears_date(self):
        self.server.decommission_date = timezone.localdate()
        self.server.save()
        response = self.client.post(reverse("server:restore", args=[self.server.pk]))
        self.assertRedirects(response, reverse("server:index"))
        self.server.refresh_from_db()
        self.assertIsNone(self.server.decommission_date)
        self.assertFalse(self.server.is_decommissioned)

    def test_list_shows_lifecycle_badge(self):
        response = self.client.get(reverse("server:index"))
        self.assertContains(response, "lifecycle01")
        self.assertContains(response, "Active")

        self.server.decommission_date = timezone.localdate()
        self.server.save()
        response = self.client.get(reverse("server:index"))
        self.assertContains(response, "Decommissioned")

    def test_bulk_decommission(self):
        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        status = Status.objects.create(name="Active")
        domain = Domain.objects.create(name="bulk-lifecycle.example.com")
        server2 = Server.objects.create(
            hostname="lifecycle02", status=status, domain=domain
        )
        response = self.client.post(
            reverse("server:bulk_action"),
            {"selected_ids": [self.server.pk, server2.pk], "decommission": "on"},
        )
        self.assertRedirects(response, reverse("server:index"))
        self.server.refresh_from_db()
        server2.refresh_from_db()
        self.assertIsNotNone(self.server.decommission_date)
        self.assertIsNotNone(server2.decommission_date)

    def test_decommission_requires_permission(self):
        from django.contrib.auth.models import User

        user = User.objects.create_user("noperm", password=PASSWORD)
        user.groups.clear()  # drop personal workspace
        self.client.logout()
        self.client.force_login(user)
        response = self.client.post(
            reverse("server:decommission", args=[self.server.pk])
        )
        # The user lacks the change permission, so the request is denied and
        # the decommission never happens.
        self.assertIn(response.status_code, [302, 403])
        self.server.refresh_from_db()
        self.assertIsNone(self.server.decommission_date)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class LifecycleApiTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Lifecycle API Group")
        self.user = User.objects.create_user("lifeapi", password=PASSWORD)
        self.user.groups.add(self.group)
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get(app_label="server", model="model")
        self.group.permissions.add(
            *Permission.objects.filter(
                content_type=ct,
                codename__in=["view_model", "add_model", "change_model"],
            )
        )
        from status.models import Model as Status
        from domain.models import Model as Domain

        self.status = Status.objects.create(name="In use")
        self.domain = Domain.objects.create(name="lifeapi.example.com")

    def test_api_exposes_decommission_date(self):
        from rest_framework.test import APIClient
        from sm.models import ApiKey
        from server.models import Model as Server

        key, secret = ApiKey.create_for_user(self.user, "life")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"ApiKey {key.client_id}:{secret}")

        server = Server.objects.create(
            hostname="lifeapi01",
            status=self.status,
            domain=self.domain,
            group=self.group,
            decommission_date=timezone.localdate(),
        )
        response = client.get(f"/api/servers/{server.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["decommission_date"],
            str(timezone.localdate()),
        )
