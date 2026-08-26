from django.test import TransactionTestCase as TestCase
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.urls import reverse

from .models import Model

from . import app_label

from sm.utils import random_string

import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "sm.settings"
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
        self.assertEqual(created, True, "the object was already there?")
        self.assertIsInstance(obj, self.model, "object not correct model!?")

    def test_name(self):
        self.assertEqual(self.testitem.name, self.teststring, "name not correct")

    def test___str__(self):
        self.assertEqual(
            "%s" % self.testitem.name,
            "%s" % self.teststring,
            "string representation not correct",
        )

    def test_absolute_url(self):
        self.assertEqual(
            "%s" % (self.testitem.get_absolute_url()),
            "%s" % (reverse("%s:detail" % app_label, kwargs={"pk": self.testitem.pk})),
            "absolute url not built correctly",
        )


class GlobalUniquenessTest(TestCase):
    """
    Global (group=None) reference rows must stay globally unique: PostgreSQL
    treats NULLs as distinct, so the group-inclusive constraint alone would
    allow duplicate global rows (which also break natural-key lookups).
    """

    model = Model
    fixtures = ["%s/fixtures/01_initial.yaml" % app_label]

    def setUp(self):

        self.group_a = Group.objects.create(name="gA-%s" % random_string())
        self.group_b = Group.objects.create(name="gB-%s" % random_string())

    def _make(self, name, group):
        return self.model.objects.create(name=name, group=group)

    def test_duplicate_global_row_rejected(self):
        key = "global-%s" % random_string()
        self._make(key, None)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self._make(key, None)

    def test_same_identity_allowed_across_groups(self):
        key = "tenant-%s" % random_string()
        a = self._make(key, self.group_a)
        b = self._make(key, self.group_b)
        self.assertNotEqual(a.pk, b.pk)
