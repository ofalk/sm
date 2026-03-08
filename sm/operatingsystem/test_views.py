from django.contrib import messages
from django.test import TestCase
from django.test import Client

from . models import Model
from vendor.models import Model as VendorModel
from . forms import FormDisabled
from . forms import Form
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist
try:
    from django.urls import reverse
except Exception as e:  # pragma: no cover
    from django.urls import reverse  # pragma: no cover


from sm.utils import random_string

import os
import django


class Tester(TestCase):
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
        username = random_string()
        self.user = User.objects.create_user(
            username=username,
            password=self.password,
        )

        self.vendor = VendorModel.objects.all().first()
        self.testitem, created = Model.objects.get_or_create(
            version=self.teststring,
            vendor=self.vendor,
        )

    def test_login_redir(self):
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_listview(self):
        Model.objects.all().delete()
        self.setUp()
        self.login()
        response = self.client.get(reverse('%s:index' % app_label))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.version,
                         self.teststring)
        self.assertEqual(item.vendor.name,
                         self.vendor.name)

    def test_detailview(self):
        self.login()
        url = reverse('%s:detail' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/detail/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.version, self.teststring)
        self.assertEqual(item.vendor.name, self.vendor.name)
        form = response.context[-1]['form']
        self.assertIsInstance(form, FormDisabled)
        for field in ['version', 'vendor']:
            self.assertTrue(form.fields[field].widget.attrs['disabled'])

    def test_updateview(self):
        self.login()
        url = reverse('%s:update' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/update/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.version, self.teststring)
        self.assertEqual(item.vendor.name, self.vendor.name)
        form = response.context[-1]['form']
        self.assertIsInstance(form, Form)
        for field in ['version', 'vendor']:
            self.assertRaises(KeyError,
                              form.fields[field].widget.attrs.__getitem__,
                              'disabled')

    def test_deleteview(self):
        self.login()
        url = reverse('%s:delete' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/delete/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.version, self.teststring)
        self.assertEqual(item.vendor.name, self.vendor.name)
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
        self.assertContains(response,
                            '%s was deleted successfully' %
                            self.testitem.version)
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(version=self.testitem.version, vendor=self.vendor)

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
                          form.fields['version'].widget.attrs.__getitem__,
                          'disabled')

    def test_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            'version': self.teststring,
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
        self.assertEqual(item.version,
                         data['version'])
        self.assertEqual(item.vendor.pk,
                         data['vendor'])
        self.assertEqual(item.vendor.name,
                         self.vendor.name)

        self.assertIsInstance(item, Model)
        self.assertContains(response, '%s was created successfully' % data['version'])

    def test_listview_empty_true_wo_obj(self):
        self.login()
        # Set cookie!
        self.client.cookies['srvmanager-show_empty'] = 'true'
        # Make sure we have no objects in there
        Model.objects.all().delete()
        response = self.client.get(reverse('%s:index' % app_label))
        item = response.context[-1]['object_list'].first()
        self.assertIsNone(item)

    def test_listview_empty_false_w_obj(self):
        self.login()
        # Set cookie!
        self.client.cookies['srvmanager-show_empty'] = 'false'
        # Make sure we have objects in there
        Model.objects.all().delete()
        self.setUp()
        self.login() # Need to login again since setUp created a NEW user
        response = self.client.get(reverse('%s:index' % app_label))
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.version,
                         self.teststring)
        self.assertEqual(item.vendor.name,
                         self.vendor.name)
