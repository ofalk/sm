from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APIClient

PASSWORD = "password123"

FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


def view_perm(app_label):
    return Permission.objects.get(
        content_type=ContentType.objects.get(app_label=app_label, model="model"),
        codename="view_model",
    )


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SearchMultiTenancyFixTest(TestCase):
    """Search results must respect group partitioning for vendors too."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Search A")
        self.group_b = Group.objects.create(name="Search B")
        self.user = User.objects.create_user("searcher", password=PASSWORD)
        self.user.groups.add(self.group_a)
        self.group_a.permissions.add(view_perm("vendor"))
        self.client.force_login(self.user)
        from vendor.models import Model as Vendor

        Vendor.objects.create(name="Alpha-Vendor", group=self.group_a)
        Vendor.objects.create(name="Beta-Vendor", group=self.group_b)

    def test_search_vendors_partitioned(self):
        response = self.client.get(reverse("search") + "?q=vendor")
        self.assertContains(response, "Alpha-Vendor")
        self.assertNotContains(response, "Beta-Vendor")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class DashboardMultiTenancyFixTest(TestCase):
    """Dashboard vendor/os counts must respect the user's groups."""

    def setUp(self):
        self.group_a = Group.objects.create(name="Dash A")
        self.group_b = Group.objects.create(name="Dash B")
        self.user = User.objects.create_user("dashfix", password=PASSWORD)
        self.user.groups.add(self.group_a)
        self.group_a.permissions.add(view_perm("vendor"))
        self.client.force_login(self.user)
        from vendor.models import Model as Vendor

        Vendor.objects.create(name="My Vendor", group=self.group_a)
        Vendor.objects.create(name="Their Vendor", group=self.group_b)

    def test_dashboard_vendor_count_filtered(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["vendor_count"], 1)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ApiClusterPackageGlobalTest(TestCase):
    """ClusterPackage API must include packages on global (null-group) clusters."""

    def setUp(self):
        self.group = Group.objects.create(name="CP Group")
        self.user = User.objects.create_user("cpuser", password=PASSWORD)
        self.user.groups.add(self.group)
        for perm in ("view_model",):
            self.group.permissions.add(
                Permission.objects.get(
                    content_type=ContentType.objects.get(
                        app_label="clusterpackage", model="model"
                    ),
                    codename=perm,
                )
            )
        from cluster.models import Model as Cluster
        from clusterpackage.models import Model as ClusterPackage
        from clusterpackagetype.models import Model as ClusterPackageType
        from status.models import Model as Status

        self.global_cluster = Cluster.objects.create(name="Global Cluster")
        self.pkg_type = ClusterPackageType.objects.create(name="RW")
        self.status = Status.objects.create(name="In use")
        ClusterPackage.objects.create(
            name="db",
            cluster=self.global_cluster,
            package_type=self.pkg_type,
            status=self.status,
        )
        from .models import ApiKey

        self.key, self.secret = ApiKey.create_for_user(self.user, "cp")

    def test_global_cluster_packages_visible(self):
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"ApiKey {self.key.client_id}:{self.secret}"
        )
        response = client.get("/api/clusterpackages/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        names = [p["name"] for p in data["results"]]
        self.assertIn("db", names)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class InvitationUniqueConstraintFixTest(TestCase):
    """Re-inviting an expired invitation must not raise IntegrityError."""

    def setUp(self):
        self.group = Group.objects.create(name="Reinvite Group")
        self.owner = User.objects.create_user("reowner", password=PASSWORD)
        self.group.profile.owner = self.owner
        self.group.profile.save()
        self.client.login(username="reowner", password=PASSWORD)
        from .models import Invitation
        from django.utils import timezone

        self.old = Invitation.objects.create(
            email="again@example.com", group=self.group, created_by=self.owner
        )
        self.old.created_at = timezone.now() - timezone.timedelta(hours=48)
        self.old.save(update_fields=["created_at"])

    def test_reinvite_after_expiry_no_integrity_error(self):
        response = self.client.post(
            reverse("group_member_invite", args=[self.group.pk]),
            {"email": "again@example.com"},
        )
        # Either redirect (success) or 200 with a friendly message - never 500.
        self.assertIn(response.status_code, [200, 302])
        from .models import Invitation

        self.assertEqual(
            Invitation.objects.filter(
                email="again@example.com", group=self.group
            ).count(),
            1,
        )
