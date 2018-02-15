from django.test import TransactionTestCase as TestCase
from django.urls import reverse

from . models import Model

from . import app_label

from sm.utils import random_string

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class Tester(TestCase):
    model = Model
    teststring = random_string()
    fixtures = []

    testitem = None

    def setUp(self):
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            name=self.teststring,
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

    def test___str__(self):
        self.assertEqual('%s' % self.testitem.name,
                         '%s' % self.teststring,
                         'string representation not correct')

    def test_absolute_url(self):
        self.assertEqual('%s' % (self.testitem.get_absolute_url()),
                         '%s' % (reverse('%s:detail' % app_label,
                                         kwargs={'pk': self.testitem.pk})),
                         'absolute url not built correctly')
