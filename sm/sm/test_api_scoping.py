from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def grant(group, app, *codenames):
    ct = ContentType.objects.get(app_label=app, model="model")
    group.permissions.add(
        *Permission.objects.filter(content_type=ct, codename__in=codenames)
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiDuplicateScopingTest(TestCase):
    def api(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_group_member_can_duplicate_global_name(self):
        # A group member's create is scoped to their group, so a group-scoped
        # item may share a name with a global one (matches web behavior).
        from status.models import Model as Status

        Status.objects.create(name="In use")  # global
        group = Group.objects.create(name="Scoping Group")
        grant(group, "status", "view_model", "add_model")
        user = User.objects.create_user("scoper", password=PASSWORD)
        user.groups.add(group)
        r = self.api(user).post("/api/statuses/", {"name": "In use"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        created = Status.objects.get(name="In use", group=group)
        self.assertEqual(created.group, group)

    def test_user_with_no_group_global_duplicate_blocked(self):
        from status.models import Model as Status

        Status.objects.create(name="Global Only")  # global
        user = User.objects.create_user("nogrp", password=PASSWORD)
        user.groups.clear()  # drop personal workspace
        from django.contrib.auth.models import Permission as P

        ct = ContentType.objects.get(app_label="status", model="model")
        user.user_permissions.add(*P.objects.filter(content_type=ct))
        r = self.api(user).post(
            "/api/statuses/", {"name": "Global Only"}, format="json"
        )
        self.assertIn(r.status_code, (400, 403), r.content)
        self.assertEqual(Status.objects.filter(name="Global Only").count(), 1)

    def test_duplicate_within_same_group_blocked(self):
        from status.models import Model as Status

        group = Group.objects.create(name="Dup Group Scope")
        grant(group, "status", "view_model", "add_model")
        Status.objects.create(name="Dup In Group", group=group)
        user = User.objects.create_user("dupinscope", password=PASSWORD)
        user.groups.add(group)
        r = self.api(user).post(
            "/api/statuses/", {"name": "Dup In Group"}, format="json"
        )
        self.assertEqual(r.status_code, 400, r.content)
        self.assertEqual(
            Status.objects.filter(name="Dup In Group", group=group).count(), 1
        )

    def test_location_duplicate_by_name_and_country(self):
        from location.models import Model as Location

        group = Group.objects.create(name="Loc Group")
        grant(group, "location", "view_model", "add_model")
        Location.objects.create(name="Berlin", country="DE", group=group)
        user = User.objects.create_user("locdup", password=PASSWORD)
        user.groups.add(group)
        r = self.api(user).post(
            "/api/locations/",
            {"name": "Berlin", "country": "DE"},
            format="json",
        )
        self.assertEqual(r.status_code, 400, r.content)

    def test_location_same_name_different_country_allowed(self):
        from location.models import Model as Location

        group = Group.objects.create(name="Loc Group 2")
        grant(group, "location", "view_model", "add_model")
        Location.objects.create(name="Springfield", country="US", group=group)
        user = User.objects.create_user("locok", password=PASSWORD)
        user.groups.add(group)
        r = self.api(user).post(
            "/api/locations/",
            {"name": "Springfield", "country": "DE"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
