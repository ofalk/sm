from django.test import TestCase


from .models import Model
from cluster.models import Model as ClusterModel
from status.models import Model as StatusModel
from clusterpackagetype.models import Model as ClusterpackagetypeModel
from .forms import FormDisabled
from .forms import Form
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

try:
    from django.urls import reverse
except Exception:  # pragma: no cover
    from django.urls import reverse  # pragma: no cover


from sm.utils import random_string


class Tester(TestCase):
    testitem = None
    password = random_string()
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

    def login(self):
        """
        Login as user
        """
        self.client.login(username=self.user.username, password=self.password)

    def setUp(self):
        """
        Create user
        Create some item in models for testing
        """
        self.user = User.objects.create_user(
            username=random_string(),
            password=self.password,
        )

        self.status = StatusModel.objects.all().first()
        self.cluster = ClusterModel.objects.all().first()
        self.package_type = ClusterpackagetypeModel.objects.all().first()
        self.testitem, created = Model.objects.get_or_create(
            name=self.teststring,
            cluster=self.cluster,
            package_type=self.package_type,
            status=self.status,
            description=self.testdescription,
            host=self.testhost,
        )

    def test_login_redir(self):
        response = self.client.get(reverse("%s:index" % app_label))
        self.assertEqual(response.status_code, 302, "no redirect?")

    def test_listview(self):
        Model.objects.all().delete()
        self.setUp()
        self.login()
        response = self.client.get(reverse("%s:index" % app_label))
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object_list"].first()
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.description, self.testdescription)
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.cluster.name, self.cluster.name)

    def test_detailview(self):
        self.login()
        url = reverse("%s:detail" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/detail/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.description, self.testdescription)
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.cluster.name, self.cluster.name)
        form = response.context[-1]["form"]
        self.assertIsInstance(form, FormDisabled)
        for field in ["name", "description", "cluster", "status"]:
            self.assertTrue(form.fields[field].widget.attrs["disabled"])

    def test_updateview(self):
        self.login()
        url = reverse("%s:update" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/update/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.description, self.testdescription)
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.cluster.name, self.cluster.name)
        form = response.context[-1]["form"]
        self.assertIsInstance(form, Form)
        for field in ["name", "description", "status", "cluster"]:
            self.assertRaises(
                KeyError, form.fields[field].widget.attrs.__getitem__, "disabled"
            )

    def test_deleteview(self):
        self.login()
        url = reverse("%s:delete" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/delete/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.description, self.testdescription)
        self.assertEqual(item.name, self.teststring)
        self.assertEqual(item.cluster.name, self.cluster.name)
        if "Are you sure you want to" not in response.content.decode("utf-8"):
            print(f"FAILED TO FIND MESSAGE IN: {response.content.decode('utf-8')}")
        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, "Confirm Delete")

    def test_deleteview_post(self):
        self.login()
        response = self.client.post(
            reverse("%s:delete" % app_label, args=[self.testitem.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200, "no status 200?")
        self.assertRedirects(response, reverse("%s:index" % app_label), status_code=302)
        pass
        self.assertContains(
            response, "%s was deleted successfully" % self.testitem.name
        )
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(
                name=self.testitem.name,
                cluster=self.cluster,
            )

    def test_createview(self):
        self.login()
        url = reverse("%s:create" % app_label)
        self.assertEqual("/%s/create" % app_label, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        self.assertRaises(KeyError, response.context[-1].__getitem__, "object")
        self.assertIn("form", response.context[-1])
        form = response.context[-1]["form"]
        self.assertRaises(
            KeyError, form.fields["description"].widget.attrs.__getitem__, "disabled"
        )

    def test_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            "name": self.teststring,
            "cluster": self.cluster.pk,
            "package_type": self.package_type.pk,
            "status": self.status.pk,
            "description": self.testdescription,
            "host": self.testhost,
        }
        response = self.client.post(
            reverse("%s:create" % app_label),
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200, "no status 200?")
        self.assertRedirects(response, reverse("%s:index" % app_label), status_code=302)
        item = response.context[-1]["object_list"].first()
        self.assertEqual(item.description, data["description"])
        self.assertEqual(item.name, data["name"])
        self.assertEqual(item.cluster.pk, data["cluster"])
        self.assertEqual(item.cluster.name, self.cluster.name)

        self.assertIsInstance(item, Model)
        if "%s was created successfully" % data["name"] not in response.content.decode(
            "utf-8"
        ):
            print(f"FAILED TO FIND MESSAGE IN: {response.content.decode('utf-8')}")
        self.assertContains(response, "%s was created successfully" % data["name"])
