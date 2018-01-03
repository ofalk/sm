from django.test import TestCase
from django.test import Client

from . models import Model
from clustersoftware.models import Model as ClustersoftwareModel
from . forms import FormDisabled
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist
try:
    from django.core.urlresolvers import reverse
except Exception as e:
    from django.urls import reverse

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
    fixtures = [
        'sm/fixtures/02_groups.yaml',
        '%s/fixtures/01_initial.yaml' % 'vendor',
        '%s/fixtures/01_initial.yaml' % 'clustersoftware',
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

        self.clustersoftware = ClustersoftwareModel.objects.all().order_by(
            'name').first()
        self.testitem, created = Model.objects.get_or_create(
            name=self.teststring,
            clustersoftware=self.clustersoftware,
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
        self.assertEqual(item.name,
                         self.teststring)
        self.assertEqual(item.clustersoftware.pk,
                         self.clustersoftware.pk)

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
        for field in ['name', 'clustersoftware']:
            self.assertTrue(form.fields[field].widget.attrs['readonly'])

    def test_updateview(self):
        self.login()
        url = reverse('%s:update' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/update/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.post(url, {
            'name': self.testitem.name,
            'clustersoftware': self.testitem.clustersoftware.pk,
        })
        self.assertRedirects(response,
                             reverse('%s:index' % app_label),
                             status_code=302)

        url = reverse('%s:detail' % app_label, args=[self.testitem.pk])
        response = self.client.get(url)
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.clustersoftware.name, self.clustersoftware.name)
        form = response.context[-1]['form']
        self.assertIsInstance(form, FormDisabled)
        for field in ['name', 'clustersoftware']:
            self.assertTrue(form.fields[field].widget.attrs['readonly'])

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
                            '%s was deleted successfully' %
                            self.testitem.name)
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(
                name=self.testitem.name,
                clustersoftware=self.clustersoftware
            )

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
            'clustersoftware': self.clustersoftware.pk,
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
        self.assertEqual(item.name,
                         data['name'])
        self.assertEqual(item.clustersoftware.pk,
                         data['clustersoftware'])

        self.assertIsInstance(item, Model)
        self.assertContains(response,
                            '%s was created successfully' % data['name'])
