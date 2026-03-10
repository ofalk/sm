from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.test import Client
import os
import django
import random
import string

import unittest
from django.conf import settings

# os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
# django.setup()


@unittest.skipIf(
    not getattr(settings, "SOCIALACCOUNT_ENABLED", False), "Social auth is disabled"
)
class SocialAuthTestCase(TestCase):
    def setUp(self):
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp

        self.user = get_user_model().objects.create_user(
            username="testuser", password="password123"
        )
        # site = Site.objects.get_current()
        # Site.objects.get_current() might fail in some test envs if SITE_ID is not matched
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        app, _ = SocialApp.objects.get_or_create(
            provider="facebook",
            defaults={"name": "Facebook", "client_id": "12345", "secret": "67890"},
        )
        app.sites.add(site)

    def test_load(self):
        # Allauth doesn't have social_tags, it uses socialaccount tags
        string = "{% load socialaccount %}"
        rendered = Template(string).render(Context({}))
        self.assertEqual(rendered, "")

    def test_can_connect(self):
        c = Client()
        c.force_login(self.user)
        # Allauth social accounts list
        r = c.get("/accounts/3rdparty/")
        self.assertEqual(200, r.status_code)
        # Check if facebook login link is present
        self.assertContains(r, "facebook")
