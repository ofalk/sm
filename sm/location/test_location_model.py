import unittest

from location.models import Location as Model

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(unittest.TestCase):
    model = Model
    name = 'Virtual123XXX'

    def test_1_creation(self):
        item, created = self.model.objects.get_or_create(name=self.name)
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, self.model, 'object not a Location model!')

    def test_2_name(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual(item.name, self.name, 'name not correct')

    def test_3_name___str___wo_country(self):
        item = self.model.objects.get(name=self.name)
        self.assertEqual("%s" % item.name, self.name, 'name not correct')

    def test_4___str___w_country(self):
        item = self.model.objects.get(name=self.name)
        item.country = 'Austria'
        self.assertEqual("%s" % item, '%s / Austria' % self.name,
                         'name not correct')

    def test_4___str___w_nonexistant_country(self):
        item = self.model.objects.get(name=self.name)
        item.country = 'Mars'
        self.assertEqual("%s" % item, '%s / Mars' % self.name,
                         'name not correct')

    def test_5_nonexisting_country(self):
        item = self.model.objects.get(name=self.name)
        item.country = 'Mars'
        self.assertEqual(item.country.flag_url, None)

    def test_6___str__wo_country(self):
        item = self.model.objects.get(name=self.name)
        item.country = None
        self.assertEqual(item.__str__(), self.name)

    def test_7_delete(self):
        item = self.model.objects.get(name=self.name)
        res = item.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('sm.Location' in res[1])
        self.assertEqual(res[1]['sm.Location'], 1)
