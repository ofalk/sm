from django.test import TestCase
from django.test import Client

from domain.models import Domain as DomainModel
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    client = Client()
    testring = 'domain.tld'

    def login(self):
        """
        Login as user 'john'
        """
        self.client.login(username='john', password='johnpassword')

    def setUp(self):
        """
        Create user
        Create some item in models for testing
        """
        self.user = User.objects.create_user('john',
                                             'lennon@thebeatles.com',
                                             'johnpassword')
        item, created = DomainModel.objects.get_or_create(name=self.testring)

    def test_01_login_redir(self):
        response = self.client.get(reverse('domain:index'))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_02_listview(self):
        self.login()
        response = self.client.get(reverse('domain:index'))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, DomainModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.testring)
