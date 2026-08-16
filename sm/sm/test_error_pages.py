from django.test import TestCase, override_settings
from django.urls import reverse

PASSWORD = "password123"


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class ErrorPageTemplatesTest(TestCase):
    def test_404_page(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Not Found", status_code=404)

    def test_404_custom_template(self):
        response = self.client.get("/definitely/missing/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class SecurityHeadersTest(TestCase):
    def test_security_headers_present(self):
        from django.test import Client

        client = Client()
        response = client.get(reverse("health"))
        # Clickjacking protection is enabled via middleware.
        self.assertTrue(response.has_header("X-Frame-Options"))
        # SecurityMiddleware sets Referrer-Policy / COOP.
        self.assertTrue(
            response.has_header("Referrer-Policy")
            or response.has_header("Cross-Origin-Opener-Policy")
        )
        # Content-Type sniffing protection.
        self.assertTrue(response.has_header("X-Content-Type-Options"))

    def test_health_endpoint_ok(self):
        from django.test import Client

        client = Client()
        response = client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertIn("database", response.json()["checks"])
