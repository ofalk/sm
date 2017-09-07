from django.test import TransactionTestCase as TestCase

from . models import Model
from . import app_label

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(TestCase):
    model = Model
    teststring = '123XXX'

    @classmethod
    def createTestItem(self):
        item, created = self.model.objects.get_or_create(
            name=self.teststring
        )
        return (item, created)

    def test_01_creation(self):
        (item, created) = self.createTestItem()
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, Model, 'object not a Location model!?')

    def test_02_name(self):
        (item, created) = self.createTestItem()
        self.assertEqual(item.name, self.teststring, 'name not correct')

    def test_03___str__(self):
        (item, created) = self.createTestItem()
        self.assertEqual("%s" % item, self.teststring,
                         'name not correct')

    def test_04_get_absolute_url(self):
        (item, created) = self.createTestItem()
        self.assertEqual('/%s/detail/%i/' % (app_label, item.id),
                         item.get_absolute_url(),
                         'reverse url not correct')
