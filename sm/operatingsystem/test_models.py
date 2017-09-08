from django.test import TransactionTestCase as TestCase

from operatingsystem.models import Model
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
                '%s/fixtures/01_initial.yaml' % app_label
                ]
    testitem = None

    def setUp(self):
        self.vendor = VendorModel.objects.all().first()
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            version=self.teststring,
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

    def test___str__(self):
        self.assertEqual("%s %s" % (self.vendor.name, self.teststring),
                         "%s %s" % (self.testitem.vendor.name,
                                    self.testitem.version),
                         'string representation not correct')

    # Class specific tests
    def test_natural_key__(self):
        self.assertEqual(self.testitem.natural_key(),
                         (self.vendor.name, self.teststring))

    def test_nothing_exception(self):
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            self.model.objects.get_by_natural_key()
        self.assertTrue('Nothing to query' in str(context.exception))

    def test_get_rhel_7_by_nat_key(self):
        item = self.model.objects.get_by_natural_key('RHEL 7')
        self.assertIsInstance(item, self.model,
                              'object not correct model!?')

    def test_get_rhel_7_by_nat_key2(self):
        item = self.model.objects.get_by_natural_key('Red Hat 7.0')
        self.assertIsInstance(item, self.model,
                              'object not correct model!?')

    def test_get_rhel_7_by_nat_key3(self):
        item = self.model.objects.get_by_natural_key('Red Hat7')
        self.assertIsInstance(item, self.model,
                              'object not correct model!?')

    def test_get_sles10_nat_key(self):
        vendor = VendorModel.objects.get_by_natural_key('Novell')
        item, created = self.model.objects.get_or_create(vendor=vendor,
                                                         version='10.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')
        item = self.model.objects.get_by_natural_key('SLES 10.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_nat_key_funny_doesnt_exist(self):
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            self.model.objects.get_by_natural_key('Hugo Boss 7.0')
        self.assertTrue('matching query does not exist' in
                        str(context.exception))

    def test_nat_key_vendor_version_exists(self):
        item = self.model.objects.get_by_natural_key(
            vendor=self.vendor.name,
            version=self.teststring)
        self.assertIsInstance(item, self.model,
                              'object not correct model!?')

    def test_nat_key_get_with_tuple(self):
        item = self.model.objects.get_by_natural_key(
            ('%s' % self.vendor.name, self.teststring))
        self.assertIsInstance(item, self.model,
                              'object not correct model!?')

    def test_query_with_dict_exception(self):
        with self.assertRaises(Exception) as context:
            self.model.objects.get_by_natural_key({})
        self.assertTrue("No idea how to handle query with <class 'dict'>" in
                        str(context.exception))

    def test_get_absolute_url(self):
        self.assertEqual('/%s/detail/%i/' % (app_label, self.testitem.id),
                         self.testitem.get_absolute_url(),
                         'reverse url not correct')
