from django.contrib import messages
from django.test import TestCase
from django.test import Client

from .models import Model
from .forms import FormDisabled
from .forms import Form
from . import app_label

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

try:
    from django.urls import reverse
except Exception as e:  # pragma: no cover
    from django.urls import reverse  # pragma: no cover

from sm.utils import random_string

import os
import django


class Tester(TestCase):
    teststring = random_string()
    testitem = None

    def login(self):
        """
        Login as user 'john'
        """
        self.client.login(username="john", password="johnpassword")

    def setUp(self):
        """
        Create user
        Create some item in models for testing
        """
        self.user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "johnpassword"
        )
        self.testitem, created = Model.objects.get_or_create(
            name=self.teststring,
        )

    def test_login_redir(self):
        response = self.client.get(reverse("%s:index" % app_label))
        self.assertEqual(response.status_code, 302, "no redirect?")

    def test_listview(self):
        self.login()
        response = self.client.get(reverse("%s:index" % app_label))
        self.assertEqual(response.status_code, 200, "no status 200?")
        objs = response.context[-1]["object_list"]
        item = objs.first()
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.name, self.teststring)

    def test_detailview(self):
        self.login()
        url = reverse("%s:detail" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/detail/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]["form"]
        self.assertIsInstance(form, FormDisabled)
        self.assertTrue(form.fields["name"].widget.attrs["disabled"])

    def test_updateview(self):
        self.login()
        url = reverse("%s:update" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/update/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.name, self.teststring)
        form = response.context[-1]["form"]
        self.assertIsInstance(form, Form)
        self.assertRaises(
            KeyError, form.fields["name"].widget.attrs.__getitem__, "disabled"
        )

    def test_deleteview(self):
        self.login()
        url = reverse("%s:delete" % app_label, args=[self.testitem.pk])
        self.assertEqual("/%s/delete/%i/" % (app_label, self.testitem.pk), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "no status 200?")
        item = response.context[-1]["object"]
        self.assertIsInstance(item, Model, "object not the correct model!?")
        self.assertEqual(item.name, self.teststring)
        if "Are you sure you want to" not in response.content.decode("utf-8"):
            print("Message not found")
        self.assertContains(response, "Are you sure you want to")
        if "<strong>delete</strong>" not in response.content.decode("utf-8"):
            print("Message not found")
        self.assertContains(response, "<strong>delete</strong>")

    def test_deleteview_post(self):
        self.login()
        response = self.client.post(
            reverse("%s:delete" % app_label, args=[self.testitem.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200, "no status 200?")
        self.assertRedirects(response, reverse("%s:index" % app_label), status_code=302)
        pass
        from django.contrib.messages import get_messages

        msgs = list(get_messages(response.wsgi_request))
        if (
            "%s was deleted successfully" % self.testitem.name
            not in response.content.decode("utf-8")
        ):
            print("Message not found")
        self.assertContains(
            response, "%s was deleted successfully" % self.testitem.name
        )
        with self.assertRaises(ObjectDoesNotExist):
            Model.objects.get(name=self.testitem.name)

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
            KeyError, form.fields["name"].widget.attrs.__getitem__, "disabled"
        )

    def test_createview_post(self):
        # Make sure we have no objects in there
        Model.objects.all().delete()
        self.login()
        data = {
            "name": self.teststring,
        }
        response = self.client.post(
            reverse("%s:create" % app_label),
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200, "no status 200?")
        self.assertRedirects(response, reverse("%s:index" % app_label), status_code=302)
        objs = response.context[-1]["object_list"]
        item = objs.first()
        self.assertEqual(item.name, data["name"])
        self.assertIsInstance(item, Model)
        if "%s was created successfully" % data["name"] not in response.content.decode(
            "utf-8"
        ):
            print("Message not found")
        self.assertContains(response, "%s was created successfully" % data["name"])
