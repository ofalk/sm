import unittest

from operatingsystem.models import Operatingsystem as Model

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(unittest.TestCase):
    model = Model

    def test_01_creation(self):
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Red Hat')
        item, created = self.model.objects.get_or_create(
            vendor=vendor,
            version='123XXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_02_version(self):
        item = self.model.objects.get(version='123XXX')
        self.assertEqual(item.version, '123XXX', 'name not correct')

    def test_03__str__(self):
        item = self.model.objects.get(version='123XXX')
        self.assertEqual("%s" % item, 'Red Hat 123XXX', 'name not correct')

    def test_04__natural_key__(self):
        item = self.model.objects.get(version='123XXX')
        self.assertEqual(item.natural_key(), ('Red Hat', '123XXX'))

    def test_05_nothing_exception(self):
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            self.model.objects.get_by_natural_key()
        self.assertTrue('Nothing to query' in str(context.exception))

    def test_06_get_or_create_rhel_7(self):
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Red Hat')
        item, created = self.model.objects.get_or_create(
            vendor=vendor,
            version='7.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_07_get_rhel_7_by_nat_key(self):
        item = self.model.objects.get_by_natural_key('RHEL 7')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_08_get_rhel_7_by_nat_key2(self):
        item = self.model.objects.get_by_natural_key('Red Hat 7.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_09_get_rhel_7_by_nat_key3(self):
        item = self.model.objects.get_by_natural_key('Red Hat7')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_10_get_or_create_sles_10(self):
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Novell')
        item, created = self.model.objects.get_or_create(vendor=vendor,
                                                         version='10.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_11_get_sles_10_by_nat_key(self):
        item = self.model.objects.get_by_natural_key('SLES 10.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_12_nat_key_funny_doesnt_exist(self):
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            self.model.objects.get_by_natural_key('Hugo Boss 7.0')
        self.assertTrue('Cannot find matching object' in
                        str(context.exception))

    def test_13_nat_key_vendor_version_exists(self):
        item = self.model.objects.get_by_natural_key(
            vendor='Red Hat',
            version='7.0')
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_14_natkey_get_with_tuple(self):
        item = self.model.objects.get_by_natural_key(('Red Hat', '7.0'))
        self.assertIsInstance(item, self.model,
                              'object not a Operatingsystem model!?')

    def test_15_query_with_dict_exception(self):
        with self.assertRaises(Exception) as context:
            self.model.objects.get_by_natural_key({})
        self.assertTrue("No idea how to handle query with <class 'dict'>" in
                        str(context.exception))

    def test_16_get_absolute_url(self):
        item = self.model.objects.get(version='123XXX')
        self.assertEqual('/operatingsystem/detail/%i/' % item.id,
                         item.get_absolute_url(),
                         'reverse url not correct')

    def test_17_get_initial(self):
        from vendor.models import Vendor as VendorModel
        from operatingsystem.views import OperatingsystemCreateView as View
        v = View()
        v.kwargs = {'vendor': 'Red Hat'}
        initial = v.get_initial()
        self.assertIsInstance(initial['vendor'], VendorModel)
        self.assertEqual(initial['vendor'].name, 'Red Hat')
