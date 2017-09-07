from django.test import TransactionTestCase as TestCase

from . models import Model
from vendor.models import Model as VendorModel
from . import app_label

from sm.utils import random_string

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    model = Model
    teststring = random_string()
    fixtures = ['%s/fixtures/01_initial.yaml' % 'vendor',
                '%s/fixtures/01_initial.yaml' % app_label]
    testitem = None

    def setUp(self):
        self.vendor = VendorModel.objects.all().first()
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            name=self.teststring,
            vendor=self.vendor,
        )
        return (self.testitem, created)

    def test_create(self):
        # Since we want to test if creation works, we
        # need to manually prune the DB and create a testitem
        self.model.objects.all().delete()
        obj, created = self.get_or_create_testitem()
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(obj, self.model,
                              'object not correct model!?')

    def test_name(self):
        self.assertEqual(self.testitem.name, self.teststring,
                         'name not correct')

    def test_name___str__(self):
        self.assertEqual("%s %s" % (self.vendor.name, self.teststring),
                         "%s %s" % (self.testitem.vendor.name,
                                    self.testitem.name),
                         'name not correct')

    def test_get_absolute_url(self):
        self.assertEqual('/%s/detail/%i/' % (app_label, self.testitem.id),
                         self.testitem.get_absolute_url(),
                         'reverse url not correct')

    def test_delete(self):
        res = self.testitem.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('%s.Model' % app_label in res[1])
        self.assertEqual(res[1]['%s.Model' % app_label], 1)
