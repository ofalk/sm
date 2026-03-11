from django.test import TransactionTestCase as TestCase
from django.urls import reverse

from .models import Model
from cluster.models import Model as ClusterModel
from patchtime.models import Model as PatchtimeModel
from location.models import Model as LocationModel
from servermodel.models import Model as ServermodelModel
from domain.models import Model as DomainModel
from status.models import Model as StatusModel
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
        "%s/fixtures/01_initial.yaml" % "domain",
        "%s/fixtures/01_initial.yaml" % "location",
        "%s/fixtures/01_initial.yaml" % "status",
        "%s/fixtures/01_initial.yaml" % "operatingsystem",
        "%s/fixtures/01_initial.yaml" % "clustersoftware",
        "%s/fixtures/01_initial.yaml" % "patchtime",
        "%s/fixtures/01_initial.yaml" % "cluster",
        "%s/fixtures/01_initial.yaml" % "servermodel",
    ]
    testitem = None

    def setUp(self):
        self.cluster = ClusterModel.objects.all().first()
        self.patchtime = PatchtimeModel.objects.all().first()
        self.location = LocationModel.objects.all().first()
        self.servermodel = ServermodelModel.objects.all().first()
        self.domain = DomainModel.objects.all().first()
        self.status = StatusModel.objects.all().first()
        self.testitem, created = self.get_or_create_testitem()

    def get_or_create_testitem(self):
        self.testitem, created = self.model.objects.get_or_create(
            hostname=self.teststring,
            cluster=self.cluster,
            patchtime=self.patchtime,
            location=self.location,
            servermodel=self.servermodel,
            domain=self.domain,
            status=self.status,
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
        self.assertEqual(self.testitem.hostname, self.teststring, "name not correct")

    def test__str__(self):
        self.assertEqual(
            "%s" % (self.teststring),
            "%s" % (self.testitem.hostname),
            "string representation not correct",
        )

    def test_absolute_url(self):
        self.assertEqual(
            "%s" % (self.testitem.get_absolute_url()),
            "%s" % (reverse("%s:detail" % app_label, kwargs={"pk": self.testitem.pk})),
            "aboslute url not built correctly",
        )
