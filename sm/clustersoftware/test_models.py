from django.test import TransactionTestCase as TestCase

from . models import Model
from vendor.models import Model as VendorModel

from . import app_label

from sm.utils import random_string, random_number

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    model = Model
    testversion = "%s.%s" % (random_number(), random_number())
    teststring = random_string()
    fixtures = ['%s/fixtures/01_initial.yaml' % 'vendor',
                '%s/fixtures/01_initial.yaml' % app_label
                ]
    testitem = None

    def setUp(self):
        self.vendor = VendorModel.objects.all().first()
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            version=self.testversion,
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

    def test_version(self):
        self.assertEqual(self.testitem.version, self.teststring,
                         'version not correct')

    def test_name(self):
        self.assertEqual(self.testitem.name, self.teststring,
                         'name not correct')

    def test___str__(self):
        self.assertEqual("%s %s %s" % (self.vendor.name,
                                       self.teststring,
                                       self.testversion),
                         "%s %s %s" % (self.testitem.vendor.name,
                                       self.testitem.name,
                                       self.testitem.version),
                         'string representation not correct')
