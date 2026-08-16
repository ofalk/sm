from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def grant(group, app, *codenames):
    ct = ContentType.objects.get(app_label=app, model="model")
    group.permissions.add(
        *Permission.objects.filter(content_type=ct, codename__in=codenames)
    )


class SearchTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpassword")

    def test_search_ajax_nav(self):
        """
        Test that AJAX search returns navigation quick jumps.
        """
        response = self.client.get(reverse("search"), {"q": "dash", "ajax": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        self.assertTemplateUsed(response, "search_results_ajax.html")

    def test_search_full_nav(self):
        """
        Test that full search page includes navigation quick jumps.
        """
        response = self.client.get(reverse("search"), {"q": "server"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servers")
        self.assertTemplateUsed(response, "search.html")

    def test_search_too_short(self):
        """
        Test behavior when query is too short.
        """
        response = self.client.get(reverse("search"), {"q": "a"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query too short")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class BroaderSearchTest(TestCase):
    """Search must cover all reference models, partitioned by group."""

    def setUp(self):
        self.group = Group.objects.create(name="Search Tenant")
        self.user = get_user_model().objects.create_user(
            username="searcher", password=PASSWORD
        )
        self.user.groups.add(self.group)
        for app in [
            "domain",
            "location",
            "status",
            "patchtime",
            "servermodel",
            "vendor",
            "operatingsystem",
            "clustersoftware",
            "clusterpackagetype",
            "cluster",
            "server",
        ]:
            grant(self.group, app, "view_model")
        self.client.force_login(self.user)

        from vendor.models import Model as Vendor
        from servermodel.models import Model as ServerModel
        from operatingsystem.models import Model as OS
        from clustersoftware.models import Model as ClusterSoftware
        from clusterpackagetype.models import Model as ClusterPackageType
        from cluster.models import Model as Cluster

        self.vendor = Vendor.objects.create(name="SearchVendor", group=self.group)
        self.servermodel = ServerModel.objects.create(
            name="SearchBlade", vendor=self.vendor, group=self.group
        )
        self.os = OS.objects.create(
            version="SearchOS 1", vendor=self.vendor, group=self.group
        )
        self.soft = ClusterSoftware.objects.create(
            name="SearchSoft", version="2.0", vendor=self.vendor, group=self.group
        )
        self.cpt = ClusterPackageType.objects.create(
            name="SearchType", group=self.group
        )
        self.cluster = Cluster.objects.create(
            name="SearchCluster", clustersoftware=self.soft, group=self.group
        )

    def _search(self, q):
        return self.client.get(reverse("search"), {"q": q})

    def test_domains_searchable(self):
        from domain.models import Model as Domain

        Domain.objects.create(name="foundme.example.com", group=self.group)
        response = self._search("foundme")
        self.assertContains(response, "foundme.example.com")

    def test_locations_searchable(self):
        from location.models import Model as Location

        Location.objects.create(name="Searchville", country="DE", group=self.group)
        response = self._search("Searchville")
        self.assertContains(response, "Searchville")

    def test_statuses_searchable(self):
        from status.models import Model as Status

        Status.objects.create(name="Search-Only-Status", group=self.group)
        response = self._search("Search-Only")
        self.assertContains(response, "Search-Only-Status")

    def test_patchtimes_searchable(self):
        from patchtime.models import Model as Patchtime

        Patchtime.objects.create(name="Search Window", group=self.group)
        response = self._search("Search Window")
        self.assertContains(response, "Search Window")

    def test_servermodels_searchable(self):
        response = self._search("SearchBlade")
        self.assertContains(response, "SearchBlade")

    def test_os_searchable(self):
        response = self._search("SearchOS")
        self.assertContains(response, "SearchOS")

    def test_clustersoftware_searchable(self):
        response = self._search("SearchSoft")
        self.assertContains(response, "SearchSoft")

    def test_clusterpackagetype_searchable(self):
        response = self._search("SearchType")
        self.assertContains(response, "SearchType")

    def test_clusters_searchable(self):
        response = self._search("SearchCluster")
        self.assertContains(response, "SearchCluster")

    def test_servers_searchable(self):
        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        status = Status.objects.create(name="Active", group=self.group)
        domain = Domain.objects.create(name="s.example.com", group=self.group)
        Server.objects.create(
            hostname="searchhost01", status=status, domain=domain, group=self.group
        )
        response = self._search("searchhost01")
        self.assertContains(response, "searchhost01")

    def test_search_respects_tenancy(self):
        from domain.models import Model as Domain

        other = Group.objects.create(name="Other Tenant")
        Domain.objects.create(name="secret-other.example.com", group=other)
        response = self._search("secret-other")
        self.assertNotContains(response, "secret-other.example.com")

    def test_search_ajax_includes_reference_results(self):
        from domain.models import Model as Domain

        Domain.objects.create(name="ajax-find.example.com", group=self.group)
        response = self.client.get(reverse("search"), {"q": "ajax-find", "ajax": "1"})
        self.assertContains(response, "ajax-find.example.com")
        self.assertTemplateUsed(response, "search_results_ajax.html")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SearchRefinementTest(TestCase):
    """Search must match server IPs, serials, related fields, and allow a
    group filter with relevance ordering."""

    def setUp(self):
        self.group = Group.objects.create(name="Refine Group")
        self.user = get_user_model().objects.create_user(
            username="refiner", password=PASSWORD
        )
        self.user.groups.add(self.group)
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        ct = ContentType.objects.get(app_label="server", model="model")
        self.group.permissions.add(*Permission.objects.filter(content_type=ct))
        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        self.status = Status.objects.create(name="Active", group=self.group)
        self.domain = Domain.objects.create(name="refine.example.com", group=self.group)
        self.server = Server.objects.create(
            hostname="refinehost01",
            status=self.status,
            domain=self.domain,
            group=self.group,
            primary_ip="10.55.66.77",
            management_ip="192.168.1.50",
            serial_nr="SN-REFINE-99",
            description="refine web server",
            application="nginx",
            rack="R-7",
        )
        self.client.force_login(self.user)

    def _search(self, q):
        return self.client.get(reverse("search"), {"q": q})

    def test_search_by_primary_ip(self):
        response = self._search("10.55.66.77")
        self.assertContains(response, "refinehost01")

    def test_search_by_management_ip(self):
        response = self._search("192.168.1.50")
        self.assertContains(response, "refinehost01")

    def test_search_by_serial(self):
        response = self._search("SN-REFINE-99")
        self.assertContains(response, "refinehost01")

    def test_search_by_application(self):
        response = self._search("nginx")
        self.assertContains(response, "refinehost01")

    def test_search_by_domain(self):
        response = self._search("refine.example.com")
        self.assertContains(response, "refinehost01")

    def test_search_exact_hostname_ranks_first(self):
        from server.models import Model as Server

        # A substring match that is alphabetically first, to ensure the
        # exact match still sorts ahead.
        Server.objects.create(
            hostname="aaa-refinehost01x",
            status=self.status,
            domain=self.domain,
            group=self.group,
        )
        response = self._search("refinehost01")
        servers = response.context["servers"]
        self.assertIsInstance(servers, list)
        self.assertEqual(servers[0].hostname, "refinehost01")

    def test_group_filter_form_present(self):
        response = self._search("refine")
        self.assertContains(response, "Filter by group")
        self.assertContains(response, "Refine Group")

    def test_group_filter_redirect(self):
        from django.contrib.auth.models import Group

        g2 = Group.objects.create(name="Refine Group 2")
        self.user.groups.add(g2)
        response = self.client.post(
            reverse("group_filter"),
            {"group": str(g2.pk), "next": reverse("search") + "?q=refine"},
        )
        self.assertRedirects(response, reverse("search") + "?q=refine")
        self.assertEqual(self.client.session["selected_groups"], [str(g2.pk)])
