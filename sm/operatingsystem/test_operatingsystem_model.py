import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class OperatingsystemTestCase(unittest.TestCase):
    def test_0_import(self):
        from operatingsystem.models import Operatingsystem as OSModel
        self.assertEqual(OSModel, OSModel, 'import went wrong')

    def test_01_creation(self):
        from operatingsystem.models import Operatingsystem as OSModel
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Red Hat')
        os, created = OSModel.objects.get_or_create(
            vendor=vendor,
            version='123XXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_02_version(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get(version='123XXX')
        self.assertEqual(os.version, '123XXX', 'name not correct')

    def test_03__str__(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get(version='123XXX')
        self.assertEqual("%s" % os, 'Red Hat 123XXX', 'name not correct')

    def test_04__natural_key__(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get(version='123XXX')
        self.assertEqual(os.natural_key(), ('Red Hat', '123XXX'))

    def test_05_nothing_exception(self):
        from operatingsystem.models import Operatingsystem as OSModel
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            OSModel.objects.get_by_natural_key()
        self.assertTrue('Nothing to query' in str(context.exception))

    def test_06_get_or_create_rhel_7(self):
        from operatingsystem.models import Operatingsystem as OSModel
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Red Hat')
        os, created = OSModel.objects.get_or_create(
            vendor=vendor,
            version='7.0')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_07_get_rhel_7_by_nat_key(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key('RHEL 7')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_08_get_rhel_7_by_nat_key2(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key('Red Hat 7.0')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_09_get_rhel_7_by_nat_key3(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key('Red Hat7')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_10_get_or_create_sles_10(self):
        from operatingsystem.models import Operatingsystem as OSModel
        from vendor.models import Vendor as VendorModel
        vendor, created = VendorModel.objects.get_or_create(name='Novell')
        OSModel.objects.get_or_create(vendor=vendor, version='10.0')

    def test_11_get_sles_10_by_nat_key(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key('SLES 10.0')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_12_nat_key_funny_doesnt_exist(self):
        from operatingsystem.models import Operatingsystem as OSModel
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist) as context:
            OSModel.objects.get_by_natural_key('Hugo Boss 7.0')
        self.assertTrue('Cannot find matching object' in
                        str(context.exception))

    def test_13_nat_key_vendor_version_exists(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key(
            vendor='Red Hat',
            version='7.0')
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_14_natkey_get_with_tuple(self):
        from operatingsystem.models import Operatingsystem as OSModel
        os = OSModel.objects.get_by_natural_key(('Red Hat', '7.0'))
        self.assertIsInstance(os, OSModel,
                              'object not a Operatingsystem model!?')

    def test_15_query_with_dict_exception(self):
        from operatingsystem.models import Operatingsystem as OSModel
        with self.assertRaises(Exception) as context:
            OSModel.objects.get_by_natural_key({})
        self.assertTrue("No idea how to handle query with <class 'dict'>" in
                        str(context.exception))

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from operatingsystem.models import Operatingsystem as OSModel
        try:
            osmod = OSModel.objects.get(version="123XXX")
            osmod.delete()
        except Exception as e:  # pragma: no cover
            pass  # pragma: no cover


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
