from django.test import TransactionTestCase as TestCase
from django.db import IntegrityError, transaction
from django.contrib.auth.models import Group

from .models import Model
from vendor.models import Model as VendorModel
from . import app_label

from sm.utils import random_string

import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "sm.settings"
django.setup()


class Tester(TestCase):
    model = Model
    teststring = random_string()
    fixtures = [
        "%s/fixtures/01_initial.yaml" % "vendor",
        "%s/fixtures/01_initial.yaml" % app_label,
    ]
    testitem = None

    def setUp(self):
        self.vendor = VendorModel.objects.all().first()
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            name=self.teststring,
            vendor=self.vendor,
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

    def test_name___str__(self):
        self.assertEqual(
            "{} {}".format(self.vendor.name, self.teststring),
            "{} {}".format(self.testitem.vendor.name, self.testitem.name),
            "name not correct",
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            "/%s/detail/%i/" % (app_label, self.testitem.id),
            self.testitem.get_absolute_url(),
            "reverse url not correct",
        )

    def test_delete(self):
        res = self.testitem.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue("%s.Model" % app_label in res[1])
        self.assertEqual(res[1]["%s.Model" % app_label], 1)


class GlobalUniquenessTest(TestCase):
    """
    Global (group=None) reference rows must stay globally unique: PostgreSQL
    treats NULLs as distinct, so the group-inclusive constraint alone would
    allow duplicate global rows (which also break natural-key lookups).
    """

    model = Model
    fixtures = [
        "%s/fixtures/01_initial.yaml" % "vendor",
        "%s/fixtures/01_initial.yaml" % app_label,
    ]

    def setUp(self):
        self.vendor = VendorModel.objects.all().first()
        self.group_a = Group.objects.create(name="gA-%s" % random_string())
        self.group_b = Group.objects.create(name="gB-%s" % random_string())

    def _make(self, name, group):
        return self.model.objects.create(name=name, vendor=self.vendor, group=group)

    def test_duplicate_global_row_rejected(self):
        name = "global-%s" % random_string()
        self._make(name, None)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self._make(name, None)

    def test_same_identity_allowed_across_groups(self):
        name = "tenant-%s" % random_string()
        a = self._make(name, self.group_a)
        b = self._make(name, self.group_b)
        self.assertNotEqual(a.pk, b.pk)
