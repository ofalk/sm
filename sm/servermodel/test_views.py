from django.test import TestCase
from django.test import Client

from . models import Model
from vendor.models import Model as VendorModel
from . forms import FormDisabled
from . forms import Form
from . import app_label

from http.cookies import SimpleCookie

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
    fixtures = ['%s/fixtures/01_initial.yaml' % 'vendor',
                '%s/fixtures/01_initial.yaml' % app_label
                ]

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
            password=self.password,
        )

        self.vendor = VendorModel.objects.all().order_by('name').first()
        self.testitem, created = Model.objects.get_or_create(
            name=self.teststring,
            vendor=self.vendor,
        )

    def test_login_redir(self):
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_listview(self):
        self.login()
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, VendorModel,
                              'object not the correct model!?')
        self.assertEqual(item.servermodel_set.all().first().name,
                         self.teststring)

    def test_detailview(self):
        self.login()
        url = reverse('%s:detail' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/detail/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]['form']
        self.assertIsInstance(form, FormDisabled)
        self.assertTrue(form.fields['name'].widget.attrs['readonly'])

    def test_updateview(self):
        self.login()
        url = reverse('%s:update' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/update/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]['form']
        self.assertIsInstance(form, Form)
        self.assertRaises(KeyError,
                          form.fields['name'].widget.attrs.__getitem__,
                          'readonly')

    def test_deleteview(self):
        self.login()
        url = reverse('%s:delete' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/delete/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        self.assertContains(response, 'Are you sure you want to')
        self.assertContains(response, '<strong>delete</strong>')

    def test_deleteview_post(self):
        self.login()
        response = self.client.post(
            reverse('%s:delete' % app_label, args=[self.testitem.pk]),
            follow=True
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('%s:index' % app_label),
                             status_code=302)
        self.assertIn('messages', response.context[-1])
        self.assertContains(response,
                            '%s was deleted successfully' % self.testitem.name)
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(name=self.testitem.name)

    def test_createview(self):
        self.login()
        url = reverse('%s:create' % app_label)
        self.assertEqual('/%s/create' % app_label, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRaises(KeyError,
                          response.context[-1].__getitem__,
                          'object')
        self.assertIn('form', response.context[-1])
        form = response.context[-1]['form']
        self.assertRaises(KeyError,
                          form.fields['name'].widget.attrs.__getitem__,
                          'readonly')

    def test_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            'name': self.teststring,
            'vendor': self.vendor.pk,
        }
        response = self.client.post(
            reverse('%s:create' % app_label),
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('%s:index' % app_label),
                             status_code=302)
        item = response.context[-1]['object_list'].first()
        self.assertEqual(item.servermodel_set.all().first().name, data['name'])
        self.assertIsInstance(item, VendorModel)
        self.assertIsInstance(item.servermodel_set.all().first(), Model)
        self.assertContains(response,
                            '%s was created successfully' % data['name'])

    # Class specific tests
    def test_listview_empty_true_wo_obj(self):
        Model.objects.all().delete()
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'true'})
        self.login()
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, VendorModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.vendor.name)

    def test_listview_empty_false_wo_obj(self):
        Model.objects.all().delete()
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'false'})
        self.login()
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsNone(item)

    def test_listview_empty_false_w_obj(self):
        self.client.cookies = SimpleCookie(
            {'srvmanager-show_empty': 'false'})
        self.login()
        response = self.client.get(reverse('%s:index' % app_label))
        item = response.context[-1]['object_list'].first()
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertIsInstance(item, VendorModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.vendor.name)
