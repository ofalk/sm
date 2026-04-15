from django.test import TestCase
from django.urls import reverse
import json


class HealthCheckTest(TestCase):
    def test_health_endpoint(self):
        url = reverse("health")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)
        self.assertIn("last_modification", data)
        self.assertEqual(data["checks"]["database"], "ok")
