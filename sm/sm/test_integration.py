import os
import asyncio
import tempfile
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from django.test import tag
from playwright.async_api import async_playwright
import random
import string


@tag("browser")
class FullIntegrationTest(StaticLiveServerTestCase):
    # Debug screenshots go to a temp directory so they never dirty the repo.
    screenshot_dir = os.path.join(tempfile.gettempdir(), "sm-test-screens")

    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        os.makedirs(cls.screenshot_dir, exist_ok=True)
        from django.conf import settings

        settings.ACCOUNT_EMAIL_VERIFICATION = "none"
        settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
        super().setUpClass()
        User = get_user_model()
        cls.username = "testadmin"
        cls.password = "testpass123"
        cls.user = User.objects.create_superuser(
            cls.username, "admin@example.com", cls.password
        )
        cls.user.set_password(cls.password)
        cls.user.save()
        from allauth.account.models import EmailAddress

        EmailAddress.objects.create(
            user=cls.user, email="admin@example.com", verified=True, primary=True
        )

    def setUp(self):
        # Create SocialApp records needed for allauth login tags to work
        from django.contrib.sites.models import Site
        from django.apps import apps

        if apps.is_installed("allauth.socialaccount"):
            from allauth.socialaccount.models import SocialApp

            site = Site.objects.get_current()
            SocialApp.objects.get_or_create(
                provider="facebook", name="Facebook", client_id="123", secret="abc"
            )
            for app in SocialApp.objects.all():
                app.sites.add(site)

    def random_string(self, length=8):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    async def _async_test_crud(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Login via Django session
            from django.test import Client

            client = Client()
            client.force_login(self.user)
            session_key = client.cookies["sessionid"].value
            await context.add_cookies(
                [
                    {
                        "name": "sessionid",
                        "value": session_key,
                        "domain": "localhost",
                        "path": "/",
                    }
                ]
            )

            page = await context.new_page()

            # 1. Create a Vendor (enable software)
            vendor_name = f"Vendor-{self.random_string()}"
            await page.goto(f"{self.live_server_url}/vendor/create")
            await page.fill('input[name="name"]', vendor_name)
            await page.set_checked("#id_is_software", True)
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')

            from vendor.models import Model as Vendor

            vendor1 = await asyncio.to_thread(Vendor.objects.get, name=vendor_name)

            # 2. Create a second Vendor
            vendor_name2 = f"Vendor-Safe-{self.random_string()}"
            await page.goto(f"{self.live_server_url}/vendor/create")
            await page.fill('input[name="name"]', vendor_name2)
            await page.set_checked("#id_is_software", True)
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')
            vendor2 = await asyncio.to_thread(Vendor.objects.get, name=vendor_name2)

            # 3. Create an OS
            os_version = f"OS-{self.random_string()}"
            await page.goto(f"{self.live_server_url}/operatingsystem/create")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            await page.screenshot(
                path=os.path.join(self.screenshot_dir, "os_form_ready.png")
            )

            await page.fill('input[name="version"]', os_version)
            await page.select_option('select[name="vendor"]', label=vendor_name)
            await page.screenshot(
                path=os.path.join(self.screenshot_dir, "os_form_filled.png")
            )
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')

            # 4. Test Protected Deletion (graceful message, item stays)
            await page.goto(f"{self.live_server_url}/vendor/delete/{vendor1.pk}/")
            try:
                await page.click('button:has-text("Confirm Delete")')
            except Exception:
                await page.screenshot(
                    path=os.path.join(self.screenshot_dir, "delete_confirm_fail.png")
                )
                print(f"Failed to find Confirm Delete on {page.url}")
                print(f"PAGE CONTENT: {await page.content()}")
                raise
            await page.wait_for_selector(
                "text=cannot be deleted because it is referenced by"
            )

            exists = await asyncio.to_thread(
                Vendor.objects.filter(pk=vendor1.pk).exists
            )
            self.assertTrue(exists, "Vendor 1 was deleted despite being referenced!")

            # 5. Test successful deletion of an unreferenced vendor
            v2_name = f"Vendor-Safe-{self.random_string()}"
            await page.goto(f"{self.live_server_url}/vendor/create")
            await page.fill('input[name="name"]', v2_name)
            await page.set_checked("#id_is_software", True)
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')
            vendor2 = await asyncio.to_thread(Vendor.objects.get, name=v2_name)

            await page.goto(f"{self.live_server_url}/vendor/delete/{vendor2.pk}/")
            async with page.expect_navigation():
                await page.click('button:has-text("Confirm Delete")')

            exists = await asyncio.to_thread(
                Vendor.objects.filter(pk=vendor2.pk).exists
            )
            self.assertFalse(exists, "Vendor 2 was not deleted!")

            await browser.close()

    def test_full_crud_and_safe_delete(self):
        asyncio.run(self._async_test_crud())
