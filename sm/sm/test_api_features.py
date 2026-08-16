from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


class TwoPerMinuteThrottle(UserRateThrottle):
    THROTTLE_RATES = {"user": "2/min"}


def grant(group, app, *codenames):
    ct = ContentType.objects.get(app_label=app, model="model")
    group.permissions.add(
        *Permission.objects.filter(content_type=ct, codename__in=codenames)
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiPaginationFilterTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="API Pagination Group")
        self.user = User.objects.create_user("apipag", password=PASSWORD)
        self.user.groups.add(self.group)
        grant(self.group, "server", "view_model")

        from status.models import Model as Status
        from domain.models import Model as Domain
        from server.models import Model as Server

        self.status = Status.objects.create(name="Active", group=self.group)
        self.domain = Domain.objects.create(name="pag.example.com", group=self.group)
        for i in range(30):
            Server.objects.create(
                hostname=f"pag-{i:02d}",
                status=self.status,
                domain=self.domain,
                group=self.group,
            )
        self.c = APIClient()
        self.c.force_authenticate(user=self.user)

    def test_list_is_paginated(self):
        response = self.c.get("/api/servers/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 30)
        self.assertEqual(len(data["results"]), 25)
        self.assertIn("next", data)
        self.assertIn("previous", data)

    def test_page_param(self):
        response = self.c.get("/api/servers/?page=2")
        data = response.json()
        self.assertEqual(len(data["results"]), 5)
        self.assertIsNone(data["next"])

    def test_search_filter(self):
        response = self.c.get("/api/servers/?search=pag-01")
        data = response.json()
        names = {s["hostname"] for s in data["results"]}
        self.assertIn("pag-01", names)
        self.assertNotIn("pag-02", names)

    def test_ordering(self):
        response = self.c.get("/api/servers/?ordering=-hostname")
        data = response.json()
        self.assertEqual(data["results"][0]["hostname"], "pag-29")
        self.assertEqual(data["results"][-1]["hostname"], "pag-05")

    def test_vendor_search(self):
        from vendor.models import Model as Vendor

        grant(self.group, "vendor", "view_model")
        Vendor.objects.create(name="Alpha Vendor", group=self.group)
        Vendor.objects.create(name="Beta Vendor", group=self.group)
        response = self.c.get("/api/vendors/?search=alpha")
        data = response.json()
        names = {v["name"] for v in data["results"]}
        self.assertEqual(names, {"Alpha Vendor"})


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiThrottleTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Throttle Group")
        self.user = User.objects.create_user("throttler", password=PASSWORD)
        self.user.groups.add(self.group)
        grant(self.group, "status", "view_model")
        self.c = APIClient()
        self.c.force_authenticate(user=self.user)

    def test_user_throttle_limits_requests(self):
        from rest_framework import status
        from sm.api.views import StatusViewSet
        from unittest import mock
        from django.core.cache import cache

        # The LocMemCache persists across tests in the same process, so clear
        # any leftover throttle state before exercising the limit.
        cache.clear()

        # View classes capture throttle_classes at import time, so patch the
        # view directly to exercise the throttle through the request path.
        with mock.patch.object(
            StatusViewSet, "throttle_classes", [TwoPerMinuteThrottle]
        ):
            # First two requests succeed
            for _ in range(2):
                response = self.c.get("/api/statuses/")
                self.assertEqual(response.status_code, 200)
            # Third is throttled
            response = self.c.get("/api/statuses/")
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
