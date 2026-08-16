from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User
from django.contrib.admin.sites import site
from django.urls import reverse

from .models import GroupProfile, ApiKey
from .views_avatars import avatar_proxy
from .context_processors import theme_settings
from .forms_admin import GroupProfileForm
from .utils import get_email_hash, random_string

PASSWORD = "password123"

FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class StaffAdminViewsTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            "staffer", password=PASSWORD, is_staff=True
        )
        self.user = User.objects.create_user("normal", password=PASSWORD)
        self.group = Group.objects.create(name="Admin Group")
        self.client.login(username="staffer", password=PASSWORD)

    def test_user_list_requires_staff(self):
        self.client.logout()
        self.client.login(username="normal", password=PASSWORD)
        response = self.client.get(reverse("user_management_list"))
        self.assertEqual(response.status_code, 403)

    def test_user_list_staff_ok(self):
        response = self.client.get(reverse("user_management_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "staffer")
        self.assertContains(response, "Admin Group")

    def test_group_profile_edit_staff_ok(self):
        profile = self.group.profile
        response = self.client.post(
            reverse("group_profile_edit", args=[profile.pk]),
            {"owner": self.user.pk, "max_items": 500, "max_users": 20},
        )
        self.assertRedirects(response, reverse("user_management_list"))
        profile.refresh_from_db()
        self.assertEqual(profile.max_items, 500)
        self.assertEqual(profile.max_users, 20)

    def test_group_profile_edit_requires_staff(self):
        self.client.logout()
        self.client.login(username="normal", password=PASSWORD)
        profile = self.group.profile
        response = self.client.get(reverse("group_profile_edit", args=[profile.pk]))
        self.assertEqual(response.status_code, 403)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ProfilePageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("profileuser", password=PASSWORD)
        self.client.login(username="profileuser", password=PASSWORD)

    def test_profile_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_get(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Profile")

    def test_profile_update(self):
        response = self.client.post(
            reverse("profile"),
            {"first_name": "Falko", "last_name": "Test", "email": "pf@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Falko")
        self.assertEqual(self.user.last_name, "Test")
        self.assertEqual(self.user.email, "pf@example.com")

    def test_profile_duplicate_email_rejected(self):
        User.objects.create_user("other", email="taken@example.com", password=PASSWORD)
        response = self.client.post(
            reverse("profile"),
            {"first_name": "", "last_name": "", "email": "taken@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "")


class DashboardViewTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Dash Group")
        self.user = User.objects.create_user("dashuser", password=PASSWORD)
        self.user.groups.add(self.group)
        self.client.login(username="dashuser", password=PASSWORD)
        from vendor.models import Model as Vendor
        from operatingsystem.models import Model as OS

        vendor = Vendor.objects.create(name="Dash Vendor", group=self.group)
        Vendor.objects.create(name="Global Vendor")
        Vendor.objects.create(name="Group Vendor", group=self.group)
        OS.objects.create(version="9", vendor=vendor, group=self.group)

    def test_dashboard_counts_respect_tenancy(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        for app in ("vendor", "operatingsystem"):
            ct = ContentType.objects.get(app_label=app, model="model")
            view_perm = Permission.objects.get(content_type=ct, codename="view_model")
            self.group.permissions.add(view_perm)

        response = self.client.get(reverse("dashboard"))
        context = response.context
        self.assertEqual(context["server_count"], 0)
        self.assertEqual(context["cluster_count"], 0)
        # Dash Vendor (group), Global Vendor and Group Vendor are all visible.
        self.assertEqual(context["vendor_count"], 3)
        self.assertEqual(context["os_count"], 1)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class HistoryDiffViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("histuser", password=PASSWORD)
        self.client.login(username="histuser", password=PASSWORD)
        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="h.example.com")
        self.server = Server.objects.create(
            hostname="hist01", status=self.status, domain=self.domain
        )
        self.server.description = "changed"
        self.server.save()

    def test_history_diff_renders(self):
        record = self.server.history.order_by("-history_date").first()
        response = self.client.get(
            reverse(
                "history_diff",
                args=["server", "model", record.history_id],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hist01")

    def test_history_diff_unknown_404(self):
        response = self.client.get(
            reverse("history_diff", args=["server", "model", 999999])
        )
        self.assertEqual(response.status_code, 404)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class StarterPackViewTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Pack Group")
        self.user = User.objects.create_user("packuser", password=PASSWORD)
        self.user.groups.add(self.group)
        self.client.login(username="packuser", password=PASSWORD)

    def test_starter_pack_import(self):
        from vendor.models import Model as Vendor

        Vendor.objects.filter(group=self.group).delete()
        response = self.client.post(reverse("starter_pack_import"))
        self.assertRedirects(response, reverse("vendor:index"))
        self.assertGreater(Vendor.objects.filter(group=self.group).count(), 0)


class AvatarProxyTest(TestCase):
    def test_get_email_hash(self):
        self.assertEqual(
            get_email_hash("Test@Example.com"), get_email_hash("test@example.com")
        )
        self.assertEqual(
            get_email_hash(""),
            "00000000000000000000000000000000",
        )

    def test_avatar_proxy_caches_and_serves(self):
        import requests

        fake = requests.Response()
        fake.status_code = 200
        fake.headers["Content-Type"] = "image/png"
        fake._content = b"\x89PNGfake"

        from unittest import mock

        with mock.patch("requests.get", return_value=fake) as m:
            response = avatar_proxy(
                type("R", (), {"GET": {}})(), get_email_hash("a@b.c")
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"\x89PNGfake")
            self.assertEqual(
                response["Cache-Control"],
                "public, max-age=604800, immutable",
            )
            m.assert_called_once()


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class UtilsAndMiscTest(TestCase):
    def test_random_string(self):
        s = random_string(10)
        self.assertEqual(len(s), 10)

    def test_group_profile_form_fields(self):
        form = GroupProfileForm()
        self.assertEqual(set(form.fields.keys()), {"owner", "max_items", "max_users"})

    def test_context_processor_theme(self):
        result = theme_settings(type("R", (), {"user": None})())
        self.assertEqual(result["THEME_GITHUB_URL"], "https://github.com/ofalk/sm")
        self.assertIn("APP_VERSION", result)
        self.assertIn("ONBOARDING_NEEDED", result)
        self.assertFalse(result["ONBOARDING_NEEDED"])

    def test_api_key_repr(self):
        user = User.objects.create_user("apikeyuser", password=PASSWORD)
        key, _ = ApiKey.create_for_user(user, "Test Key")
        self.assertEqual(str(key), "Test Key")

    def test_admin_registration(self):
        # GroupProfile, Invitation, ApiKey registered in the Django admin.
        self.assertIn(GroupProfile, site._registry)
        self.assertIn(ApiKey, site._registry)

    def test_admin_registration_all_models(self):
        """Every core model must be registered in the Django admin."""
        from django.apps import apps

        for app_label in [
            "server",
            "cluster",
            "clusterpackage",
            "clusterpackagetype",
            "clustersoftware",
            "domain",
            "location",
            "operatingsystem",
            "patchtime",
            "servermodel",
            "status",
            "vendor",
        ]:
            model = apps.get_model(app_label, "Model")
            self.assertIn(
                model,
                site._registry,
                f"{app_label}.Model is not registered in the Django admin",
            )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SelectedGroupsSessionTest(TestCase):
    def setUp(self):
        self.group_a = Group.objects.create(name="Session A")
        self.group_b = Group.objects.create(name="Session B")
        self.user = User.objects.create_user("sessionuser", password=PASSWORD)
        self.user.groups.add(self.group_a, self.group_b)
        self.client.login(username="sessionuser", password=PASSWORD)
        from vendor.models import Model as Vendor

        Vendor.objects.create(name="Vendor A", group=self.group_a)
        Vendor.objects.create(name="Vendor B", group=self.group_b)

    def test_session_filter_applies_to_list(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get(app_label="vendor", model="model")
        self.group_a.permissions.add(
            Permission.objects.get(content_type=ct, codename="view_model")
        )
        self.group_b.permissions.add(
            Permission.objects.get(content_type=ct, codename="view_model")
        )

        session = self.client.session
        session["selected_groups"] = [str(self.group_a.pk)]
        session.save()

        response = self.client.get(reverse("vendor:index"))
        self.assertContains(response, "Vendor A")
        self.assertNotContains(response, "Vendor B")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class PaginationTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Page Group")
        self.user = User.objects.create_superuser("pageadmin", "a@b.c", PASSWORD)
        self.client.force_login(self.user)
        from vendor.models import Model as Vendor

        for i in range(26):
            Vendor.objects.create(name=f"Page Vendor {i:02d}")

    def test_list_paginates(self):
        response = self.client.get(reverse("vendor:index"))
        self.assertEqual(response.status_code, 200)
        page_names = [v.name for v in response.context["object_list"]]
        self.assertIn("Page Vendor 00", page_names)
        self.assertNotIn("Page Vendor 25", page_names)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["paginator"].num_pages, 2)

    def test_second_page(self):
        response = self.client.get(reverse("vendor:index") + "?page=2")
        self.assertEqual(response.status_code, 200)
        page_names = [v.name for v in response.context["object_list"]]
        self.assertIn("Page Vendor 25", page_names)
