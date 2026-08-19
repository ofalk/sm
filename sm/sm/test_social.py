from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.test import Client

import unittest
from types import SimpleNamespace
from unittest import mock

from django.conf import settings


@unittest.skipIf(
    not getattr(settings, "SOCIALACCOUNT_ENABLED", False),
    "Social auth is disabled",
)
class SocialAuthTestCase(TestCase):
    def setUp(self):
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp

        self.user = get_user_model().objects.create_user(
            username="testuser", password="password123"
        )
        # site = Site.objects.get_current()
        # Site.objects.get_current() might fail in some test envs
        # if SITE_ID is not matched
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        app, _ = SocialApp.objects.get_or_create(
            provider="google",
            defaults={"name": "Google", "client_id": "12345", "secret": "67890"},
        )
        app.sites.add(site)

    def test_load(self):
        # Allauth doesn't have social_tags, it uses socialaccount tags
        template_str = "{% load socialaccount %}"
        rendered = Template(template_str).render(Context({}))
        self.assertEqual(rendered, "")

    def test_can_connect(self):
        c = Client()
        c.force_login(self.user)
        # Allauth social accounts list
        r = c.get("/accounts/3rdparty/")
        self.assertEqual(200, r.status_code)
        # Check if google login link is present
        self.assertContains(r, "google")

    def _call_pre_social_login(self, email_addresses):
        from sm.adapter import MySocialAccountAdapter

        sociallogin = SimpleNamespace(
            is_existing=False,
            email_addresses=email_addresses,
            connect=mock.MagicMock(),
        )
        MySocialAccountAdapter().pre_social_login(None, sociallogin)
        return sociallogin

    def test_autolink_requires_verified_email(self):
        get_user_model().objects.create_user(
            username="victim", password="password123", email="victim@example.com"
        )
        unverified = SimpleNamespace(verified=False, email="victim@example.com")
        sociallogin = self._call_pre_social_login([unverified])
        sociallogin.connect.assert_not_called()

    def test_autolink_connects_on_verified_email(self):
        victim = get_user_model().objects.create_user(
            username="victim", password="password123", email="victim@example.com"
        )
        verified = SimpleNamespace(verified=True, email="victim@example.com")
        sociallogin = self._call_pre_social_login([verified])
        sociallogin.connect.assert_called_once_with(None, victim)

    def test_autolink_skips_verified_email_without_matching_user(self):
        verified = SimpleNamespace(verified=True, email="nobody@example.com")
        sociallogin = self._call_pre_social_login([verified])
        sociallogin.connect.assert_not_called()

    def test_autolink_skips_when_already_existing(self):
        get_user_model().objects.create_user(
            username="victim", password="password123", email="victim@example.com"
        )
        verified = SimpleNamespace(verified=True, email="victim@example.com")
        sociallogin = SimpleNamespace(
            is_existing=True,
            email_addresses=[verified],
            connect=mock.MagicMock(),
        )
        from sm.adapter import MySocialAccountAdapter

        MySocialAccountAdapter().pre_social_login(None, sociallogin)
        sociallogin.connect.assert_not_called()
