from django.test import TransactionTestCase as TestCase
from django.urls import reverse

from .models import Model
from status.models import Model as StatusModel
from cluster.models import Model as ClusterModel
from clusterpackagetype.models import Model as ClusterpackagetypeModel

from . import app_label

from sm.utils import random_string

import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "sm.settings"
django.setup()


class Tester(TestCase):
    model = Model
    testdescription = "%s" % random_string()
    testhost = "%s" % random_string()
    teststring = random_string()
    fixtures = [
        "%s/fixtures/01_initial.yaml" % "vendor",
        "%s/fixtures/01_initial.yaml" % "servermodel",
        "%s/fixtures/01_initial.yaml" % "status",
        "%s/fixtures/01_initial.yaml" % "domain",
        "%s/fixtures/01_initial.yaml" % "patchtime",
        "%s/fixtures/01_initial.yaml" % "operatingsystem",
        "%s/fixtures/01_initial.yaml" % "clustersoftware",
        "%s/fixtures/01_initial.yaml" % "cluster",
        "%s/fixtures/01_initial.yaml" % "clusterpackagetype",
    ]
    testitem = None

    def setUp(self):
        self.status = StatusModel.objects.all().first()
        self.cluster = ClusterModel.objects.all().first()
        self.package_type = ClusterpackagetypeModel.objects.all().first()
        self.description = self.testdescription
        self.host = self.testhost
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            name=self.teststring,
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            host=self.testhost,
            description=self.testdescription,
        )
        return (self.testitem, created)

    def test_create(self):
        # Since we want to test if creation works, we
        # need to manually prune the DB and create a testitem
        self.model.objects.all().delete()
        obj, created = self.get_or_create_testitem()
        self.assertEqual(created, True, "the object was already there?")
        self.assertIsInstance(obj, self.model, "object not correct model!?")

    def test_description(self):
        self.assertEqual(
            self.testitem.description, self.testdescription, "description not correct"
        )

    def test_name(self):
        self.assertEqual(self.testitem.name, self.teststring, "name not correct")

    def test_natural_key(self):
        self.assertEqual(
            (self.cluster.name, self.teststring),
            self.testitem.natural_key(),
            "natural key not correct",
        )

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
