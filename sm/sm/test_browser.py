import os
import asyncio
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import get_resolver
from django.contrib.auth import get_user_model
from playwright.async_api import async_playwright


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
                    await page.click('button[type="submit"]')
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

                # Run up to 5 concurrent checks
                semaphore = asyncio.Semaphore(5)

                async def sem_check(url):
                    async with semaphore:
                        return await check_url(url)

                tasks = [sem_check(url) for url in target_urls]
                results = await asyncio.gather(*tasks)
                all_results.extend([r for r in results if r])

                await browser.close()

            return all_results
