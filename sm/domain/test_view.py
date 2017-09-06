from django.test import TestCase
from django.test import Client

from domain.models import Domain as DomainModel
from domain.forms import DomainFormDisabled, DomainForm
from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

from django.core.urlresolvers import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    client = Client()
    teststring = 'domain.tld'

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
        item, created = DomainModel.objects.get_or_create(name=self.teststring)

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
        self.assertEqual(item.name, self.teststring)

    def test_03_detailview(self):
        self.login()
        testobj = DomainModel.objects.all().first()
        url = reverse('domain:detail', args=[testobj.pk])
        self.assertEqual('/domain/detail/%i/' % testobj.pk, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, DomainModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]['form']
        self.assertIsInstance(form, DomainFormDisabled)
        self.assertTrue(form.fields['name'].widget.attrs['readonly'])

    def test_03_updateview(self):
        self.login()
        testobj = DomainModel.objects.all().first()
        url = reverse('domain:update', args=[testobj.pk])
        self.assertEqual('/domain/update/%i/' % testobj.pk, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, DomainModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]['form']
        self.assertIsInstance(form, DomainForm)
        self.assertRaises(KeyError,
                          form.fields['name'].widget.attrs.__getitem__,
                          'readonly')

    def test_04_deleteview(self):
        self.login()
        testobj = DomainModel.objects.all().first()
        url = reverse('domain:delete', args=[testobj.pk])
        self.assertEqual('/domain/delete/%i/' % testobj.pk, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, DomainModel,
                              'object not the correct model!?')
        self.assertEqual(item.name, self.teststring)
        self.assertContains(response, 'Are you sure you want to')
        self.assertContains(response, '<strong>delete</strong>')

    def test_05_deleteview_post(self):
        self.login()
        testobj = DomainModel.objects.all().first()
        response = self.client.post(
            reverse('domain:delete', args=[testobj.pk]),
            follow=True
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('domain:index'),
                             status_code=302)
        self.assertIn('messages', response.context[-1])
        self.assertContains(response,
                            '%s was deleted successfully' % testobj.name)
        with self.assertRaises(ObjectDoesNotExist):
            DomainModel.objects.get(name=testobj.name)

    def test_06_createview(self):
        self.login()
        url = reverse('domain:create')
        self.assertEqual('/domain/create', url)
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
        DomainModel.objects.all().delete()
        self.login()
        data = {
            'name': 'newdomain.tld',
        }
        response = self.client.post(
            reverse('domain:create'),
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('domain:index'),
                             status_code=302)
        item = response.context[-1]['object_list'].first()
        self.assertEqual(item.name, data['name'])
        self.assertIsInstance(item, DomainModel)
        self.assertContains(response,
                            '%s was created successfully' % data['name'])
