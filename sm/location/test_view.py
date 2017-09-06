from django.test import TestCase
from django.test import Client

from . models import Model
from . forms import FormDisabled
from . forms import Form
from . urls import app_name

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from sm.utils import random_string

from django_countries import countries

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    client = Client()
    teststring = random_string()
    country = countries[0]

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
        item, created = Model.objects.get_or_create(
            name=self.teststring,
            country=self.country,
        )

    def test_01_login_redir(self):
        response = self.client.get(reverse('%s:index' % app_name))
        self.assertEqual(response.status_code, 302, 'no redirect?')

    def test_02_listview(self):
        self.login()
        response = self.client.get(reverse('%s:index' % app_name))
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object_list'].first()
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.country, self.country)

    def test_03_detailview(self):
        self.login()
        testobj = Model.objects.all().first()
        url = reverse('%s:detail' % app_name, args=[testobj.pk])
        self.assertEqual('/%s/detail/%i/' % (app_name, testobj.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]['form']
        self.assertIsInstance(form, FormDisabled)
        self.assertTrue(form.fields['name'].widget.attrs['readonly'])

    def test_03_updateview(self):
        self.login()
        testobj = Model.objects.all().first()
        url = reverse('%s:update' % app_name, args=[testobj.pk])
        self.assertEqual('/%s/update/%i/' % (app_name, testobj.pk), url)
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

    def test_04_deleteview(self):
        self.login()
        testobj = Model.objects.all().first()
        url = reverse('%s:delete' % app_name, args=[testobj.pk])
        self.assertEqual('/%s/delete/%i/' % (app_name, testobj.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        self.assertContains(response, 'Are you sure you want to')
        self.assertContains(response, '<strong>delete</strong>')

    def test_05_deleteview_post(self):
        self.login()
        testobj = Model.objects.all().first()
        response = self.client.post(
            reverse('%s:delete' % app_name, args=[testobj.pk]),
            follow=True
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('%s:index' % app_name),
                             status_code=302)
        self.assertIn('messages', response.context[-1])
        self.assertContains(response,
                            '%s was deleted successfully' % testobj.name)
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(name=testobj.name)

    def test_06_createview(self):
        self.login()
        url = reverse('%s:create' % app_name)
        self.assertEqual('/%s/create' % app_name, url)
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

    def test_07_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            'name': self.teststring,
            'country': self.country,
        }
        response = self.client.post(
            reverse('%s:create' % app_name),
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('%s:index' % app_name),
                             status_code=302)
        item = response.context[-1]['object_list'].first()
        self.assertEqual(item.name, data['name'])
        self.assertIsInstance(item, Model)
        self.assertContains(response,
                            '%s was created successfully' % data['name'])
