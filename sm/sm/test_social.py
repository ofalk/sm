from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.test import Client
import os
import django
import random
import string

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

    def test_02_cannot_disconnect_password_missing(self):
        from social_django.models import UserSocialAuth as SocialModel
        socuser = SocialModel(user=self.user)
        socuser.provider = 'facebook'
        socuser.save()
        c = Client()
        c.force_login(self.user)
        r = c.get('/account/social/accounts/', follow=True)
        # assertValidResponse:
        self.assertEqual(200, r.status_code, 'Expected a 200 status code, but'
                         ' %s was returned' % r.status_code
                         )
        self.assertContains(
            r,
            'You must set a valid password before you can disconnect.'
        )

    def test_03_can_disconnect(self):
        from social_django.models import UserSocialAuth as SocialModel
        socuser = SocialModel(user=self.user)
        socuser.provider = 'facebook'
        socuser.save()
        # Set a random password (remove spaces)
        socuser.user.set_password(
            ''.join([random.choice(string.printable)
                     for i in range(30)]).strip()
        )
        socuser.user.save()
        c = Client()
        c.force_login(self.user)
        r = c.get('/account/social/accounts/', follow=True)
        # assertValidResponse:
        self.assertEqual(200, r.status_code, 'Expected a 200 status code, but'
                         ' %s was returned' % r.status_code
                         )
        self.assertContains(
            r,
            '<button class="btn btn-danger btn-block">Disconnect '
            '<i class="fa fa-facebook"></i> Facebook</button>'
        )
