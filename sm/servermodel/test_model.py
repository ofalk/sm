import unittest

from servermodel.models import Servermodel as Model
from vendor.models import Vendor as VendorModel

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(unittest.TestCase):
    model = Model
    name = 'DL 380G9'
    vendor = None

    def setUp(self):
        self.vendor, created = VendorModel.objects.get_or_create(
            name='Hewlett Packard Enterprise')

    def test_01_creation(self):
        item, created = self.model.objects.get_or_create(
            vendor=self.vendor,
            name=self.name
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, self.model,
                              'object not a %s model!?' % self.model)

    def test_02_name(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual(item.name, self.name, 'name not correct')

    def test_03__str__(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual("%s" % item, '%s %s' % (item.vendor.name, item.name),
                         'name not correct')

    def test_04_get_absolute_url(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual('/servermodel/detail/%i/' % item.id,
                         item.get_absolute_url(),
                         'reverse url not correct')

    def test_05_get_initial(self):
        from servermodel.views import ServermodelCreateView as View
        v = View()
        v.kwargs = {'vendor': self.vendor.name}
        initial = v.get_initial()
        self.assertIsInstance(initial['vendor'], VendorModel)
        self.assertEqual(initial['vendor'].name, self.vendor.name)

    def test_06_natural_key(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual(item.natural_key(), (self.vendor.name, self.name))
