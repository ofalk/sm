from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class PermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin", email="admin@linux-kernel.at", password="password"
        )
        self.client.login(username="admin", password="password")

    def test_server_list_access(self):
        response = self.client.get(reverse("server:index"))
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
