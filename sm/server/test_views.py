from django.test import TestCase
from django.test import Client

from . models import Model
from cluster.models import Model as ClusterModel
from patchtime.models import Model as PatchtimeModel
from location.models import Model as LocationModel
from servermodel.models import Model as ServermodelModel
from domain.models import Model as DomainModel
from status.models import Model as StatusModel
from . forms import FormDisabled
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist
try:
    from django.core.urlresolvers import reverse
except Exception as e:
    from django.urls import reverse

from sm.utils import random_string

import datetime

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
                '%s/fixtures/01_initial.yaml' % 'domain',
                '%s/fixtures/01_initial.yaml' % 'location',
                '%s/fixtures/01_initial.yaml' % 'status',
                '%s/fixtures/01_initial.yaml' % 'operatingsystem',
                '%s/fixtures/01_initial.yaml' % 'clustersoftware',
                '%s/fixtures/01_initial.yaml' % 'patchtime',
                '%s/fixtures/01_initial.yaml' % 'cluster',
                '%s/fixtures/01_initial.yaml' % 'servermodel',
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
        self.cluster = ClusterModel.objects.all().order_by(
            'name').first()
        self.patchtime = PatchtimeModel.objects.all().order_by(
            'name').first()
        self.location = LocationModel.objects.all().order_by(
            'name').first()
        self.servermodel = ServermodelModel.objects.all().order_by(
            'name').first()
        self.domain = DomainModel.objects.all().order_by(
            'name').first()
        self.status = StatusModel.objects.all().order_by(
            'name').first()

        self.testitem, created = Model.objects.get_or_create(
            hostname=self.teststring,
            cluster=self.cluster,
            patchtime=self.patchtime,
            location=self.location,
            servermodel=self.servermodel,
            domain=self.domain,
            status=self.status,
            install_date=datetime.date.today(),
            delivery_date=datetime.date.today(),
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
        self.assertEqual(item.hostname,
                         self.teststring)
        self.assertEqual(item.cluster.pk,
                         self.cluster.pk)

    def test_detailview(self):
        self.login()
        url = reverse('%s:detail' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/detail/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')

    def test_updateview(self):
        self.login()
        url = reverse('%s:update' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/update/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.post(url, {
            'hostname': self.testitem.hostname,
            'cluster': self.testitem.cluster.pk,
            'status': self.testitem.status.pk,
            'location': self.testitem.location.pk,
            'servermodel': self.testitem.servermodel.pk,
            'patchtime': self.testitem.patchtime.pk,
            'domain': self.testitem.domain.pk,
            'install_date': datetime.date.today(),
            'delivery_date': datetime.date.today(),
        })
        self.assertRedirects(response,
                             reverse('%s:index' % app_label),
                             status_code=302)

        url = reverse('%s:detail' % app_label, args=[self.testitem.pk])
        response = self.client.get(url)
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'object not the correct model!?')
        self.assertEqual(item.hostname, self.teststring)
        self.assertEqual(item.cluster.name, self.cluster.name)
        form = response.context[-1]['form']
        self.assertIsInstance(form, FormDisabled)
        for field in ['hostname', 'domain', 'delivery_date', 'install_date',
                      ]:
            self.assertTrue(form.fields[field].widget.attrs['readonly'])

    def test_deleteview(self):
        self.login()
        url = reverse('%s:delete' % app_label, args=[self.testitem.pk])
        self.assertEqual('/%s/delete/%i/' % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        item = response.context[-1]['object']
        self.assertIsInstance(item, Model,
                              'oobject not the correct model!?')
        self.assertEqual(item.hostname, self.teststring)
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
                            self.testitem.hostname)
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(
                hostname=self.testitem.hostname,
            )

    def test_createview(self):
        self.login()
        url = reverse('%s:create' % app_label)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'no status 200?')
        self.assertRaises(KeyError,
                          response.context[-1].__getitem__,
                          'object')
        self.assertIn('form', response.context[-1])
        form = response.context[-1]['form']
        self.assertRaises(KeyError,
                          form.fields['hostname'].widget.attrs.__getitem__,
                          'readonly')

    def test_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            'hostname': self.testitem.hostname,
            'cluster': self.testitem.cluster.pk,
            'status': self.testitem.status.pk,
            'location': self.testitem.location.pk,
            'servermodel': self.testitem.servermodel.pk,
            'patchtime': self.testitem.patchtime.pk,
            'domain': self.testitem.domain.pk,
            'install_date': datetime.date.today(),
            'delivery_date': datetime.date.today(),
        }
        response = self.client.post(
            reverse('%s:create' % app_label),
            data,
            follow=True,
        )
        self.assertEquals(response.status_code, 200, 'no status 200?')
        self.assertRedirects(response,
                             reverse('%s:index' % app_label),
                             status_code=302)
        item = response.context[-1]['object_list'].first()
        self.assertEqual(item.hostname, data['hostname'])
        self.assertEquals(item.cluster.pk, data['cluster'])
        self.assertEquals(item.status.pk, data['status'])
        self.assertEquals(item.location.pk, data['location'])
        self.assertEquals(item.servermodel.pk, data['servermodel'])
        self.assertEquals(item.patchtime.pk, data['patchtime'])
        self.assertEquals(item.domain.pk, data['domain'])
        self.assertEquals(item.install_date, data['install_date'])
        self.assertEquals(item.delivery_date, data['delivery_date'])

        self.assertIsInstance(item, Model)
        self.assertContains(response,
                            '%s was created successfully' % data['hostname'])
