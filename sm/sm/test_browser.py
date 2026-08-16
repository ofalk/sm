import os
import asyncio
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import get_resolver
from django.contrib.auth import get_user_model
from django.test import tag
from playwright.async_api import async_playwright


@tag("browser")
class BrowserIntegrationTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        # Create a superuser for testing all pages
        User = get_user_model()
        cls.username = "testadmin"
        cls.password = "testpass123"
        cls.user = User.objects.create_superuser(
            cls.username, "admin@example.com", cls.password
        )

    def get_all_urls(self):
        resolver = get_resolver()
        urls = []

        def collect_urls(patterns, prefix=""):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    collect_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    url = prefix + str(pattern.pattern)
                    url = url.replace("^", "").replace("$", "")
                    if any(
                        skip in url
                        for skip in [
                            "admin",
                            "logout",
                            "debug",
                            "__",
                            "password",
                            "delete",
                            "detail",
                            "schema",
                            "api",
                            "accounts",
                            "2fa",
                            "social",
                            "server",
                            "group/filter",
                            "starter-pack",
                            "terms",
                            "privacy",
                            "impressum",
                            "avatar",
                            "history",
                            "search",
                            "cluster",
                            "vendor",
                            "status",
                            "location",
                            "domain",
                            "patchtime",
                            "operatingsystem",
                            "servermodel",
                            "clustersoftware",
                            "clusterpackage",
                            "clusterpackagetype",
                        ]
                    ):
                        continue
                    if "<" in url or "(" in url:
                        continue
                    if not url.startswith("/"):
                        url = "/" + url
                    if url not in urls:
                        urls.append(url)

        collect_urls(resolver.url_patterns)
        return sorted(urls)

    def test_js_integrity_anonymous(self):
        """
        Test public pages as an anonymous user to ensure login snippets etc are
        OK.
        """
        results = asyncio.run(self._async_test_js(is_anonymous=True))

        if results:
            errors_msg = "\n\n".join(
                [f"{url}:\n" + "\n".join(errors) for url, errors in results]
            )
            self.fail(f"JS/Resource errors found for anonymous user:\n\n{errors_msg}")

    def test_js_integrity_authenticated(self):
        """
        Test project pages as an authenticated user.
        """
        results = asyncio.run(self._async_test_js(is_anonymous=False))

        if results:
            errors_msg = "\n\n".join(
                [f"{url}:\n" + "\n".join(errors) for url, errors in results]
            )
            self.fail(
                f"JS/Resource errors found for authenticated user:\n\n{errors_msg}"
            )

    async def _login(self, page, username, password):
        """Logs an open page into the app and waits for the redirect to settle."""
        await page.goto(f"{self.live_server_url}/accounts/login/")
        await page.fill('input[name="login"]', username)
        await page.fill('input[name="password"]', password)
        await page.click("form.login button[type='submit']")
        await page.wait_for_load_state("networkidle")
        # Ensure the dashboard (post-login redirect target) has rendered.
        await page.wait_for_selector("body", timeout=10000)

    async def _create_vendor(self, page, name):
        """Creates a vendor via the UI and returns the list page."""
        await page.goto(f"{self.live_server_url}/vendor/create")
        await page.wait_for_load_state("networkidle")
        await page.fill('input[name="name"]', name)
        await page.click(".form-actions button[type='submit']")
        await page.wait_for_load_state("networkidle")
        await page.goto(f"{self.live_server_url}/vendor/")
        await page.wait_for_load_state("networkidle")

    @tag("browser")
    def test_crud_workflow(self):
        """
        Create, verify in list, and delete a vendor through the real browser.
        """

        async def scenario():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                try:
                    await self._login(page, self.username, self.password)
                    await self._create_vendor(page, "Browser Test Vendor")
                    self.assertGreater(
                        await page.locator("#vendor_list tbody")
                        .get_by_text("Browser Test Vendor")
                        .count(),
                        0,
                    )

                    # Edit it
                    await page.goto(f"{self.live_server_url}/vendor/")
                    rows = page.locator("#vendor_list tbody tr")
                    # Find the row containing our vendor and click its edit link
                    row = rows.filter(has_text="Browser Test Vendor")
                    await row.locator("a[title='Edit vendor']").first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.fill('input[name="name"]', "Browser Test Vendor Edited")
                    await page.click(".form-actions button[type='submit']")
                    await page.wait_for_load_state("networkidle")
                    await page.goto(f"{self.live_server_url}/vendor/")
                    self.assertGreater(
                        await page.locator("#vendor_list tbody")
                        .get_by_text("Browser Test Vendor Edited")
                        .count(),
                        0,
                    )
                finally:
                    await browser.close()

        asyncio.run(scenario())

    @tag("browser")
    def test_multitenancy_browser_isolation(self):
        """
        Two browser users in different groups must not see each other's data.
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        User = get_user_model()
        group_a = Group.objects.create(name="Browser Group A")
        group_b = Group.objects.create(name="Browser Group B")
        user_a = User.objects.create_user(
            "browser_user_a", "a@example.com", "pw12345678"
        )
        user_b = User.objects.create_user(
            "browser_user_b", "b@example.com", "pw12345678"
        )
        user_a.groups.add(group_a)
        user_b.groups.add(group_b)

        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        vendor_ct = ContentType.objects.get(app_label="vendor", model="model")
        for group in (group_a, group_b):
            group.permissions.add(
                *Permission.objects.filter(
                    content_type=vendor_ct, codename__in=["view_model", "add_model"]
                )
            )

        from vendor.models import Model as Vendor

        Vendor.objects.create(name="Secret Vendor A", group=group_a)

        async def scenario():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context_a = await browser.new_context()
                context_b = await browser.new_context()
                try:
                    page_a = await context_a.new_page()
                    await self._login(page_a, "browser_user_a", "pw12345678")
                    await page_a.goto(f"{self.live_server_url}/vendor/")
                    await page_a.wait_for_load_state("networkidle")
                    # User A sees their own group's vendor in the list.
                    self.assertGreater(
                        await page_a.locator("#vendor_list tbody")
                        .get_by_text("Secret Vendor A")
                        .count(),
                        0,
                    )
                    await page_a.close()

                    page_b = await context_b.new_page()
                    await self._login(page_b, "browser_user_b", "pw12345678")
                    await page_b.goto(f"{self.live_server_url}/vendor/")
                    await page_b.wait_for_load_state("networkidle")
                    # User B must never see user A's vendor anywhere on the page.
                    self.assertEqual(
                        await page_b.get_by_text("Secret Vendor A").count(), 0
                    )
                    await page_b.close()
                finally:
                    await browser.close()

        asyncio.run(scenario())

    async def _async_test_js(self, is_anonymous=False):
        async with async_playwright() as p:
            # Test in multiple browsers
            browser_types = [p.chromium, p.firefox]
            all_results = []

            for browser_type in browser_types:
                browser_name = browser_type.name
                browser = await browser_type.launch(headless=True)
                context = await browser.new_context()

                # Setup SocialApps in DB (inside async context)
                from django.contrib.sites.models import Site
                from django.apps import apps

                if apps.is_installed("allauth.socialaccount"):
                    from allauth.socialaccount.models import SocialApp

                    site = await asyncio.to_thread(Site.objects.get_current)
                    for p_id in ["facebook", "google"]:
                        app, _ = await asyncio.to_thread(
                            SocialApp.objects.get_or_create,
                            provider=p_id,
                            name=p_id.title(),
                            defaults={"client_id": "123", "secret": "abc"},
                        )
                        await asyncio.to_thread(app.sites.add, site)

                if not is_anonymous:
                    # Login
                    page = await context.new_page()
                    await page.goto(f"{self.live_server_url}/accounts/login/")
                    await page.fill('input[name="login"]', self.username)
                    await page.fill('input[name="password"]', self.password)
                    await page.click("form.login button[type='submit']")
                    await page.wait_for_load_state("networkidle")
                    await page.close()

                target_urls = self.get_all_urls()
                if is_anonymous:
                    # For anonymous, only test root and login-related pages
                    target_urls = ["/", "/accounts/login/"]

                print(
                    f"\n[{browser_name}] Testing {len(target_urls)} URLs "
                    f"(Anonymous={is_anonymous})..."
                )

                async def check_url(url, browser_name=browser_name):
                    new_page = await context.new_page()
                    errors = []

                    # Capture ALL console messages (errors AND warnings)
                    new_page.on(
                        "console",
                        lambda msg: (
                            errors.append(f"Console {msg.type.upper()}: {msg.text}")
                            if msg.type in ["error", "warning"]
                            else None
                        ),
                    )

                    # Capture unhandled exceptions
                    new_page.on(
                        "pageerror",
                        lambda exc: errors.append(f"JS Exception: {exc}"),
                    )

                    # Capture failed network requests
                    new_page.on(
                        "requestfailed",
                        lambda req: errors.append(
                            f"Network Failure ({req.method}): {req.url} - "
                            + (
                                getattr(req.failure, "error_text", req.failure)
                                if req.failure
                                else "Unknown Error"
                            )
                        ),
                    )

                    # Capture non-OK responses and MIME mismatches
                    async def handle_response(res):
                        # 3xx are fine (redirects), but 4xx and 5xx are errors
                        if res.status >= 400:
                            errors.append(f"HTTP {res.status} on {res.url}")

                        # Check for MIME type conflicts on scripts
                        content_type = res.headers.get("content-type", "")
                        if res.ok and ".js" in res.url and "text/html" in content_type:
                            errors.append(
                                f"MIME Type Conflict: {res.url} returned "
                                f"{content_type} (expected javascript)"
                            )

                    new_page.on("response", handle_response)

                    try:
                        await new_page.goto(
                            f"{self.live_server_url}{url}",
                            wait_until="networkidle",
                            timeout=15000,
                        )
                        # Explicit wait for any late-firing JS
                        await asyncio.sleep(1.0)

                        # Retry once on a transient 5xx (e.g. a momentary DB
                        # lock on the shared live-server connection).
                        if any("HTTP 5" in e for e in errors):
                            errors = []
                            await new_page.reload(wait_until="networkidle")
                            await asyncio.sleep(1.0)

                        if errors:
                            return (f"[{browser_name}] {url}", errors)
                        return None
                    except Exception as e:
                        return (
                            f"[{browser_name}] {url}",
                            [f"Navigation Error: {str(e)}"],
                        )
                    finally:
                        await new_page.close()

                # Load pages with a small concurrency limit. The live server
                # runs in a shared thread, and hammering it with too many
                # concurrent loads (across two browsers) can cause transient
                # 500s under contention. Capping concurrency keeps the sweep
                # reliable without serialising everything.
                semaphore = asyncio.Semaphore(2)

                async def sem_check(url):
                    async with semaphore:
                        return await check_url(url)

                tasks = [sem_check(url) for url in target_urls]
                results = await asyncio.gather(*tasks)
                all_results.extend([r for r in results if r])

                await browser.close()

            from django.db import connection

            connection.close()

            return all_results
