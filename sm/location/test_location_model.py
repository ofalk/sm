from django.test import TransactionTestCase as TestCase

from location.models import Location as Model

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    model = Model
    teststring = 'Virtual123XXX'

    @classmethod
    def createTestItem(self):
        item, created = self.model.objects.get_or_create(
           name=self.teststring
        )
        return (item, created)

    def test_01_creation(self):
        item, created = self.createTestItem()
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, self.model, 'object not a Location model!')

    def test_02_name(self):
        item, created = self.createTestItem()
        self.assertEqual(item.name, self.teststring, 'name not correct')

    def test_03_name___str___wo_country(self):
        item, created = self.createTestItem()
        self.assertEqual("%s" % item.name, self.teststring, 'name not correct')

    def test_04___str___w_country(self):
        item, created = self.createTestItem()
        item.country = 'Austria'
        self.assertEqual("%s" % item, '%s / Austria' % self.teststring,
                         'name not correct')

    def test_04___str___w_nonexistant_country(self):
        item, created = self.createTestItem()
        item.country = 'Mars'
        self.assertEqual("%s" % item, '%s / Mars' % self.teststring,
                         'name not correct')

    def test_05_nonexisting_country(self):
        item, created = self.createTestItem()
        item.country = 'Mars'
        self.assertEqual(item.country.flag_url, None)

    def test_06___str__wo_country(self):
        item, created = self.createTestItem()
        item.country = None
        self.assertEqual(item.__str__(), self.teststring)

    def test_07_delete(self):
        item, created = self.createTestItem()
        res = item.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('sm.Location' in res[1])
        self.assertEqual(res[1]['sm.Location'], 1)
