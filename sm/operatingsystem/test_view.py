from django.test import TestCase
from django.test import Client
from http.cookies import SimpleCookie

from . models import Model
from vendor.models import Vendor as VendorModel
from . forms import Form, FormDisabled
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from sm.utils import random_string

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    client = Client()
    teststring = random_string()
    testitem = None
    password = random_string()
    vendor = VendorModel.objects.all().first()

    def login(self):
        """
        Login as user
        """
        self.client.login(username=self.user.username, password=self.password)

    def setUp(self):
        """
        Create user
        Create some item in models for testing
        """
        self.user = User.objects.create_user(
            username=random_string(),
            password=self.password)

        self.testitem, created = Model.objects.get_or_create(
            name=self.teststring,
            vendor=self.vendor)

    def test_login_redir(self):
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_listview_empty_true_wo_obj(self):
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
