from django.test import TransactionTestCase as TestCase
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth.models import Group

from .models import Model
from status.models import Model as StatusModel
from cluster.models import Model as ClusterModel
from clustersoftware.models import Model as ClustersoftwareModel
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
            (
                self.cluster.name,
                self.teststring,
                self.status.name,
                self.package_type.name,
                None,
            ),
            self.testitem.natural_key(),
            "natural key not correct",
        )

    def test_get_by_natural_key(self):
        found = self.model.objects.get_by_natural_key(
            self.cluster.name,
            self.teststring,
            self.status.name,
            self.package_type.name,
            None,
        )
        self.assertEqual(found.pk, self.testitem.pk)

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

    def test_same_name_different_status_allowed(self):
        group = Group.objects.create(name="test-group")
        other_status = StatusModel.objects.create(name="other", group=group)
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.1",
            group=group,
        )
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=other_status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.2",
            group=group,
        )
        self.assertEqual(
            self.model.objects.filter(name="dup", cluster=self.cluster).count(), 2
        )

    def test_same_name_different_package_type_allowed(self):
        group = Group.objects.create(name="test-group")
        other_type = ClusterpackagetypeModel.objects.create(name="other", group=group)
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.1",
            group=group,
        )
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=other_type,
            description="desc",
            host="10.0.0.2",
            group=group,
        )
        self.assertEqual(
            self.model.objects.filter(name="dup", cluster=self.cluster).count(), 2
        )

    def test_same_name_different_clusters_allowed(self):
        group = Group.objects.create(name="test-group")
        cluster2 = ClusterModel.objects.create(
            name="cluster-2",
            clustersoftware=ClustersoftwareModel.objects.first(),
            group=group,
        )
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.1",
            group=group,
        )
        self.model.objects.create(
            name="dup",
            cluster=cluster2,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.2",
            group=group,
        )
        self.assertEqual(self.model.objects.filter(name="dup").count(), 2)

    def test_same_name_different_groups_allowed(self):
        group_a = Group.objects.create(name="group-a")
        group_b = Group.objects.create(name="group-b")
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.1",
            group=group_a,
        )
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.2",
            group=group_b,
        )
        self.assertEqual(self.model.objects.filter(name="dup").count(), 2)

    def test_same_name_status_package_type_rejected(self):
        group = Group.objects.create(name="test-group")
        self.model.objects.create(
            name="dup",
            cluster=self.cluster,
            status=self.status,
            package_type=self.package_type,
            description="desc",
            host="10.0.0.1",
            group=group,
        )
        with self.assertRaises(IntegrityError):
            self.model.objects.create(
                name="dup",
                cluster=self.cluster,
                status=self.status,
                package_type=self.package_type,
                description="desc",
                host="10.0.0.2",
                group=group,
            )
        self.assertEqual(
            self.model.objects.filter(name="dup", cluster=self.cluster).count(), 1
        )
