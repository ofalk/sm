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
class PatchScheduleTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Schedule Group")
        self.user = User.objects.create_user("scheduleuser", password=PASSWORD)
        self.user.groups.add(self.group)
        grant(self.group, "server", "view_model")
        self.client.force_login(self.user)

        from status.models import Model as Status
        from domain.models import Model as Domain
        from patchtime.models import Model as Patchtime
        from server.models import Model as Server

        self.status = Status.objects.create(name="In use", group=self.group)
        self.domain = Domain.objects.create(name="s.example.com", group=self.group)
        self.window = Patchtime.objects.create(name="Sunday 2am", group=self.group)
        Server.objects.create(
            hostname="sched01",
            status=self.status,
            domain=self.domain,
            patchtime=self.window,
            group=self.group,
        )
        Server.objects.create(
            hostname="nopatch",
            status=self.status,
            domain=self.domain,
            group=self.group,
        )

    def test_patch_schedule_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("patch_schedule"))
        self.assertEqual(response.status_code, 302)

    def test_patch_schedule_groups_servers_by_window(self):
        response = self.client.get(reverse("patch_schedule"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunday 2am")
        self.assertContains(response, "sched01")
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "nopatch")

    def test_patch_schedule_respects_tenancy(self):
        other = Group.objects.create(name="Other Schedule Group")
        from status.models import Model as Status
        from domain.models import Model as Domain
        from patchtime.models import Model as Patchtime
        from server.models import Model as Server

        status = Status.objects.create(name="Active", group=other)
        domain = Domain.objects.create(name="other.example.com", group=other)
        window = Patchtime.objects.create(name="Saturday 4am", group=other)
        Server.objects.create(
            hostname="other-secret",
            status=status,
            domain=domain,
            patchtime=window,
            group=other,
        )
        response = self.client.get(reverse("patch_schedule"))
        self.assertNotContains(response, "other-secret")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class MonitoringBadgeTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("monadmin", "m@e.c", PASSWORD)
        self.client.force_login(self.superuser)
        from status.models import Model as Status
        from domain.models import Model as Domain
        from server.models import Model as Server

        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="m.example.com")
        Server.objects.create(
            hostname="monitored",
            status=self.status,
            domain=self.domain,
            monitoring_from_puppet=True,
        )
        Server.objects.create(
            hostname="plain",
            status=self.status,
            domain=self.domain,
        )

    def test_list_shows_monitoring_badges(self):
        response = self.client.get(reverse("server:index"))
        self.assertContains(response, "Monitoring")
        self.assertContains(response, "Yes")
        self.assertContains(response, "No")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class I18NTest(TestCase):
    def test_login_page_renders_german(self):
        response = self.client.get("/accounts/login/", HTTP_ACCEPT_LANGUAGE="de")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anmelden")
        self.assertContains(response, "Passwort")

    def test_login_page_renders_english(self):
        response = self.client.get("/accounts/login/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")
