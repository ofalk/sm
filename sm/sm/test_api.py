from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from domain.models import Model as Domain
from server.models import Model as Server
from status.models import Model as Status
from vendor.models import Model as Vendor

from .models import ApiKey

PASSWORD = "password123"

FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def grant_model_perms(group, app_label, *codenames):
    """Grant a set of model permissions to a group."""
    ct = ContentType.objects.get(app_label=app_label, model="model")
    perms = Permission.objects.filter(content_type=ct, codename__in=codenames)
    group.permissions.add(*perms)


def view_perm(app_label):
    return Permission.objects.get(
        content_type=ContentType.objects.get(app_label=app_label, model="model"),
        codename="view_model",
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiKeyManagementTest(TestCase):
    """Tests for the API key management UI."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password=PASSWORD)
        self.user.groups.clear()
        self.other_user = User.objects.create_user("bob", password=PASSWORD)
        self.other_user.groups.clear()
        self.client.login(username="alice", password=PASSWORD)

    def test_requires_login(self):
        anon = APIClient()
        response = anon.get(reverse("api_keys"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response.url)

    def test_create_key_shows_secret_once(self):
        response = self.client.post(reverse("api_keys"), {"name": "my monitor"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["new_key"].name, "my monitor")
        secret = response.context["new_secret"]
        self.assertEqual(len(secret) >= 32, True)
        key = ApiKey.objects.get(user=self.user)
        self.assertEqual(key.name, "my monitor")
        # Secret is hashed, never stored in plaintext
        self.assertNotEqual(key.secret_hash, secret)
        self.assertNotIn(secret, key.secret_hash)

    def test_create_key_without_name(self):
        response = self.client.post(reverse("api_keys"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["new_key"].name, "")

    def test_secret_not_rendered_on_follow_up_request(self):
        key, secret = ApiKey.create_for_user(self.user, "hidden")
        response = self.client.get(reverse("api_keys"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, secret)

    def test_list_shows_only_own_keys(self):
        ApiKey.create_for_user(self.user, "mine")
        ApiKey.create_for_user(self.user, "mine 2")
        ApiKey.create_for_user(self.other_user, "theirs")
        response = self.client.get(reverse("api_keys"))
        self.assertEqual(response.context["api_keys"].count(), 2)
        self.assertContains(response, "mine")

    def test_revoke_key(self):
        key, _ = ApiKey.create_for_user(self.user, "to revoke")
        response = self.client.post(reverse("api_key_revoke", args=[key.pk]))
        self.assertRedirects(response, reverse("api_keys"))
        key.refresh_from_db()
        self.assertFalse(key.is_active)

    def test_cannot_revoke_other_users_key(self):
        key, _ = ApiKey.create_for_user(self.other_user, "theirs")
        response = self.client.post(reverse("api_key_revoke", args=[key.pk]))
        self.assertEqual(response.status_code, 404)
        key.refresh_from_db()
        self.assertTrue(key.is_active)

    def test_revoke_requires_post(self):
        key, _ = ApiKey.create_for_user(self.user, "to revoke")
        response = self.client.get(reverse("api_key_revoke", args=[key.pk]))
        self.assertEqual(response.status_code, 405)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiKeyAuthenticationTest(TestCase):
    """Tests for API key authentication itself."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password=PASSWORD)
        self.user.groups.clear()
        self.group = Group.objects.create(name="Auth Group")
        self.group.permissions.add(view_perm("server"))
        self.user.groups.add(self.group)
        self.key, self.secret = ApiKey.create_for_user(self.user, "auth test")

    def api(self, token=None):
        client = APIClient()
        if token:
            client.credentials(HTTP_AUTHORIZATION=token)
        return client

    def test_unauthenticated_request_returns_401(self):
        response = self.api().get("/api/servers/")
        self.assertEqual(response.status_code, 401)

    def test_valid_key_authenticates(self):
        response = self.api(f"ApiKey {self.key.client_id}:{self.secret}").get(
            "/api/servers/"
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_secret_returns_401(self):
        response = self.api(f"ApiKey {self.key.client_id}:wrong-secret").get(
            "/api/servers/"
        )
        self.assertEqual(response.status_code, 401)

    def test_unknown_client_id_returns_401(self):
        response = self.api("ApiKey unknown-client:whatever").get("/api/servers/")
        self.assertEqual(response.status_code, 401)

    def test_malformed_header_returns_401(self):
        response = self.api("ApiKey only-one-part").get("/api/servers/")
        self.assertEqual(response.status_code, 401)
        response = self.api("ApiKey").get("/api/servers/")
        self.assertEqual(response.status_code, 401)

    def test_wrong_scheme_returns_401(self):
        response = self.api("Bearer sometoken").get("/api/servers/")
        self.assertEqual(response.status_code, 401)

    def test_revoked_key_returns_401(self):
        key, secret = ApiKey.create_for_user(self.user, "revoked")
        key.is_active = False
        key.save(update_fields=["is_active"])
        response = self.api(f"ApiKey {key.client_id}:{secret}").get("/api/servers/")
        self.assertEqual(response.status_code, 401)

    def test_disabled_user_returns_401(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.api(f"ApiKey {self.key.client_id}:{self.secret}").get(
            "/api/servers/"
        )
        self.assertEqual(response.status_code, 401)

    def test_session_auth_still_works(self):
        client = APIClient()
        client.force_login(self.user)
        response = client.get("/api/servers/")
        self.assertEqual(response.status_code, 200)

    def test_last_used_at_updated(self):
        self.assertIsNone(self.key.last_used_at)
        self.api(f"ApiKey {self.key.client_id}:{self.secret}").get("/api/servers/")
        self.key.refresh_from_db()
        self.assertIsNotNone(self.key.last_used_at)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiMultiTenancyTest(TestCase):
    """Tests that API keys respect group-based data partitioning."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        self.user_a = User.objects.create_user("user_a", password=PASSWORD)
        self.user_b = User.objects.create_user("user_b", password=PASSWORD)
        self.superuser = User.objects.create_superuser(
            "super", password=PASSWORD, email="super@example.com"
        )
        for user in (self.user_a, self.user_b):
            user.groups.clear()

        for group in (self.group_a, self.group_b):
            group.permissions.add(view_perm("server"))
            group.permissions.add(view_perm("vendor"))

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
        self.server_global = Server.objects.create(
            hostname="global", status=self.status, domain=self.domain
        )
        Vendor.objects.create(name="Vendor A", group=self.group_a)
        Vendor.objects.create(name="Vendor B", group=self.group_b)

    def apiclient(self, user):
        client = APIClient()
        if user == self.user_a:
            client.credentials(
                HTTP_AUTHORIZATION=f"ApiKey {self.key_a.client_id}:{self.secret_a}"
            )
        else:
            client.credentials(
                HTTP_AUTHORIZATION=f"ApiKey {self.key_b.client_id}:{self.secret_b}"
            )
        return client

    def test_user_only_sees_own_group_data(self):
        response = self.apiclient(self.user_a).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertEqual(response.status_code, 200)
        self.assertIn("alpha", names)
        self.assertNotIn("beta", names)
        self.assertIn("global", names)  # global items are visible to everyone

    def test_other_user_has_own_partition(self):
        response = self.apiclient(self.user_b).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertIn("beta", names)
        self.assertNotIn("alpha", names)
        self.assertIn("global", names)

    def test_partitioning_applies_to_all_models(self):
        response = self.apiclient(self.user_a).get("/api/vendors/")
        names = {item["name"] for item in response.json()}
        self.assertIn("Vendor A", names)
        self.assertNotIn("Vendor B", names)

    def test_superuser_sees_everything(self):
        client = APIClient()
        client.force_login(self.superuser)
        response = client.get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertEqual(response.status_code, 200)
        self.assertIn("alpha", names)
        self.assertIn("beta", names)

    def test_cannot_fetch_other_groups_object_by_id(self):
        response = self.apiclient(self.user_a).get(f"/api/servers/{self.server_b.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_create_assigns_to_users_group(self):
        self.group_a.permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get(app_label="server", model="model"),
                codename="add_model",
            )
        )
        response = self.apiclient(self.user_a).post(
            "/api/servers/",
            {
                "hostname": "new-server",
                "status": "Active",
                "domain": "example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created = Server.objects.get(hostname="new-server")
        self.assertEqual(created.group, self.group_a)

    def test_created_items_invisible_to_other_group(self):
        self.group_a.permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get(app_label="server", model="model"),
                codename="add_model",
            )
        )
        self.apiclient(self.user_a).post(
            "/api/servers/",
            {"hostname": "private", "status": "Active", "domain": "example.com"},
            format="json",
        )
        response = self.apiclient(self.user_b).get("/api/servers/")
        names = {item["hostname"] for item in response.json()}
        self.assertNotIn("private", names)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiPermissionTest(TestCase):
    """Tests that API keys can only do what their user can do."""

    def setUp(self):
        self.group = Group.objects.create(name="View Only Group")
        self.user = User.objects.create_user("viewer", password=PASSWORD)
        self.user.groups.clear()
        self.user.groups.add(self.group)
        self.key, self.secret = ApiKey.create_for_user(self.user, "viewer")
        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="example.com")

    def apiclient(self):
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"ApiKey {self.key.client_id}:{self.secret}"
        )
        return client

    def test_no_view_permission_returns_403(self):
        self.group.permissions.clear()
        response = self.apiclient().get("/api/servers/")
        self.assertEqual(response.status_code, 403)

    def test_view_permission_allows_read(self):
        self.group.permissions.add(view_perm("server"))
        response = self.apiclient().get("/api/servers/")
        self.assertEqual(response.status_code, 200)

    def test_write_without_add_permission_returns_403(self):
        self.group.permissions.add(view_perm("server"))
        response = self.apiclient().post(
            "/api/servers/",
            {"hostname": "hacked", "status": "Active", "domain": "example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Server.objects.filter(hostname="hacked").exists())

    def test_write_with_add_permission_succeeds(self):
        self.group.permissions.add(view_perm("server"))
        self.group.permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get(app_label="server", model="model"),
                codename="add_model",
            )
        )
        response = self.apiclient().post(
            "/api/servers/",
            {"hostname": "allowed", "status": "Active", "domain": "example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_delete_without_delete_permission_returns_403(self):
        server = Server.objects.create(
            hostname="keep-me", status=self.status, domain=self.domain, group=self.group
        )
        self.group.permissions.add(view_perm("server"))
        response = self.apiclient().delete(f"/api/servers/{server.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Server.objects.filter(pk=server.pk).exists())

    def test_change_without_change_permission_returns_403(self):
        server = Server.objects.create(
            hostname="locked", status=self.status, domain=self.domain, group=self.group
        )
        self.group.permissions.add(view_perm("server"))
        response = self.apiclient().patch(
            f"/api/servers/{server.pk}/",
            {"description": "changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_group_edit_permissions_apply_to_api(self):
        # The group grants full edit perms -> API key inherits them
        ct = ContentType.objects.get(app_label="server", model="model")
        perms = Permission.objects.filter(content_type=ct)
        self.group.permissions.add(*perms)

        server = Server.objects.create(
            hostname="editable",
            status=self.status,
            domain=self.domain,
            group=self.group,
        )
        response = self.apiclient().patch(
            f"/api/servers/{server.pk}/",
            {"description": "updated via api"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        server.refresh_from_db()
        self.assertEqual(server.description, "updated via api")

        response = self.apiclient().delete(f"/api/servers/{server.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Server.objects.filter(pk=server.pk).exists())

    def test_quota_enforced_on_api_creation(self):
        ct = ContentType.objects.get(app_label="server", model="model")
        self.group.permissions.add(
            *Permission.objects.filter(
                content_type=ct, codename__in=["view_model", "add_model"]
            )
        )
        profile = self.group.profile
        profile.max_items = 1
        profile.save(update_fields=["max_items"])
        Server.objects.create(
            hostname="filler", status=self.status, domain=self.domain, group=self.group
        )

        response = self.apiclient().post(
            "/api/servers/",
            {"hostname": "over-quota", "status": "Active", "domain": "example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Server.objects.filter(hostname="over-quota").exists())
