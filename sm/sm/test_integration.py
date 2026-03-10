import os
import asyncio
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from playwright.async_api import async_playwright
import random
import string


class FullIntegrationTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
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
            await page.screenshot(path="os_form_ready.png")

            await page.fill('input[name="version"]', os_version)
            await page.select_option('select[name="vendor"]', label=vendor_name)
            await page.screenshot(path="os_form_filled.png")
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')

            # 4. Test Protected Deletion (Reassignment)
            await page.goto(f"{self.live_server_url}/vendor/delete/{vendor1.pk}/")
            try:
                await page.click('button:has-text("Confirm Delete")')
            except:
                await page.screenshot(path="delete_confirm_fail.png")
                print(f"Failed to find Confirm Delete on {page.url}")
                print(f"PAGE CONTENT: {await page.content()}")
                raise
            await page.wait_for_selector("text=Action Required: This item is in use")
            # 5. Test Reassignment
            await page.select_option('select[name="new_target"]', value=str(vendor2.pk))
            async with page.expect_navigation():
                await page.click(
                    f'button:has-text("Reassign items and delete the {vendor1.name}")'
                )

            exists = await asyncio.to_thread(
                Vendor.objects.filter(pk=vendor1.pk).exists
            )
            self.assertFalse(exists, "Vendor 1 was not deleted!")

            from operatingsystem.models import Model as OS

            os_obj = await asyncio.to_thread(OS.objects.get, version=os_version)
            v_id = await asyncio.to_thread(lambda: os_obj.vendor.id)
            self.assertEqual(v_id, vendor2.id, "OS was not reassigned to Vendor 2!")

            # 5. Test Bulk Delete (Danger Zone)
            v3_name = f"Vendor-Bulk-{self.random_string()}"
            await page.goto(f"{self.live_server_url}/vendor/create")
            await page.fill('input[name="name"]', v3_name)
            await page.set_checked("#id_is_software", True)
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')
            vendor3 = await asyncio.to_thread(Vendor.objects.get, name=v3_name)

            # Link an OS to it
            await page.goto(f"{self.live_server_url}/operatingsystem/create")
            await page.fill('input[name="version"]', f"OS-Bulk-{self.random_string()}")
            await page.select_option('select[name="vendor"]', label=v3_name)
            async with page.expect_navigation():
                await page.click('form.form button[type="submit"]')

            # Now delete Vendor 3 with "Delete All"
            await page.goto(f"{self.live_server_url}/vendor/delete/{vendor3.pk}/")
            await page.click('button:has-text("Confirm Delete")')
            await page.wait_for_selector("text=Action Required: This item is in use")

            page.once("dialog", lambda dialog: dialog.accept())
            async with page.expect_navigation():
                await page.click('button:has-text("Option 2: Delete All")')

            exists = await asyncio.to_thread(
                Vendor.objects.filter(pk=vendor3.pk).exists
            )
            self.assertFalse(exists, "Vendor 3 was not deleted!")

            await browser.close()

    def test_full_crud_and_safe_delete(self):
        asyncio.run(self._async_test_crud())
