from django.test import TestCase
from django.test import Client
from http.cookies import SimpleCookie

from operatingsystem.models import Operatingsystem as OperatingsystemModel
from vendor.models import Vendor as VendorModel
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    client = Client()

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
        vendor, created = VendorModel.objects.get_or_create(name='testvendor')

    def test_01_login_redir(self):
        response = self.client.get(reverse('operatingsystem:index'))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_02_listview_empty_true_wo_obj(self):
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'true'})
        self.login()
        response = self.client.get(reverse('operatingsystem:index'))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, VendorModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, 'testvendor')

    def test_03_listview_empty_false_wo_obj(self):
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'false'})
        self.login()
        response = self.client.get(reverse('operatingsystem:index'))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsNone(item)

    def test_04_listview_empty_false(self):
        operatingsystem, created = OperatingsystemModel.objects.get_or_create(
            vendor=VendorModel.objects.all().first(),
            version='testversion')
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'false'})
        self.login()
        response = self.client.get(reverse('operatingsystem:index'))
        item = response.context[-1]['object_list'].first()
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertIsInstance(item, VendorModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, 'testvendor')
