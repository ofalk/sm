from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class PermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.client.login(username="testuser", password="password")

    def test_server_list_access_non_superuser(self):
        # Clear automatically created personal group for this test case
        # otherwise the user has view_model permission via the personal group.
        self.user.groups.clear()

        response = self.client.get(reverse("server:index"))
        print(f"Status Code for non-superuser: {response.status_code}")
        # Expect 403 because no permissions
        self.assertEqual(response.status_code, 403)
