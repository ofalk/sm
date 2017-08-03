from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.test import Client
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser')

    def test_00_load(self):
        string = '{% load social_tags %}'
        rendered = Template(string).render(Context({}))
        self.assertEqual(rendered, '')

    def test_01_can_connect(self):
        c = Client()
        c.force_login(self.user)
        r = c.get('/account/social/accounts/', follow=True)
        # assertValidResponse:
        self.assertEqual(200, r.status_code, 'Expected a 200 status code, but'
                         ' %s was returned' % r.status_code
                         )
        self.assertContains(
            r,
            '<a class="btn btn-primary" href="/login/facebook/">Connect '
            '<i class="fa fa-facebook"></i> Facebook</a>\n'
        )
