import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class ModelTestCase(unittest.TestCase):
    def test_0_import(self):
        from vendor.models import Vendor as VendorModel
        self.assertEqual(VendorModel, VendorModel, 'import went wrong')

    def test_1_creation(self):
        from vendor.models import Vendor as VendorModel
        obj, created = VendorModel.objects.get_or_create(
            name='VendorXXXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(obj, VendorModel,
                              'object not a Vendor model!?')

    def test_2_name(self):
        from vendor.models import Vendor as VendorModel
        obj = VendorModel.objects.get(name='VendorXXXX')
        self.assertEqual(obj.name, 'VendorXXXX', 'name not correct')

    def test_3_name__str__(self):
        from vendor.models import Vendor as VendorModel
        obj = VendorModel.objects.get(name='VendorXXXX')
        self.assertEqual("%s" % obj, 'VendorXXXX', 'name not correct')

    def test_4_get_absolute_url(self):
        from vendor.models import Vendor as Model
        item = Model.objects.get(name='VendorXXXX')
        self.assertEqual('/vendor/detail/%i/' % item.id,
                         item.get_absolute_url(),
                         'reverse url not correct')

    def test_5_delete(self):
        from vendor.models import Vendor as VendorModel
        obj = VendorModel.objects.get(name='VendorXXXX')
        res = obj.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('sm.Vendor' in res[1])
        self.assertEqual(res[1]['sm.Vendor'], 1)

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from vendor.models import Vendor as VendorModel
        try:
            obj = VendorModel.objects.get(name='VendorXXXX')
            obj.delete()  # pragma: no cover
        except Exception as e:
            pass


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
