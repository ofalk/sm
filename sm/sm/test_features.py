from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User
from django.urls import reverse

PASSWORD = "password123"

FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class BulkDeleteGenericTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Bulk Group")
        self.superuser = User.objects.create_superuser("bulksuper", "s@e.c", PASSWORD)
        self.client.force_login(self.superuser)

    def test_bulk_delete_vendors(self):
        from vendor.models import Model as Vendor

        v1 = Vendor.objects.create(name="Bulk Vendor 1")
        v2 = Vendor.objects.create(name="Bulk Vendor 2")
        response = self.client.post(
            reverse("vendor:bulk_delete"),
            {"selected_ids": [v1.pk, v2.pk]},
        )
        self.assertRedirects(response, reverse("vendor:index"))
        self.assertFalse(Vendor.objects.filter(pk__in=[v1.pk, v2.pk]).exists())

    def test_bulk_delete_clusters(self):
        from cluster.models import Model as Cluster

        c1 = Cluster.objects.create(name="Bulk Cluster 1")
        c2 = Cluster.objects.create(name="Bulk Cluster 2")
        response = self.client.post(
            reverse("cluster:bulk_delete"),
            {"selected_ids": [c1.pk, c2.pk]},
        )
        self.assertRedirects(response, reverse("cluster:index"))
        self.assertFalse(Cluster.objects.filter(pk__in=[c1.pk, c2.pk]).exists())

    def test_bulk_delete_domains(self):
        from domain.models import Model as Domain

        d1 = Domain.objects.create(name="bulk-a.example.com")
        d2 = Domain.objects.create(name="bulk-b.example.com")
        response = self.client.post(
            reverse("domain:bulk_delete"),
            {"selected_ids": [d1.pk, d2.pk]},
        )
        self.assertRedirects(response, reverse("domain:index"))
        self.assertFalse(Domain.objects.filter(pk__in=[d1.pk, d2.pk]).exists())

    def test_bulk_delete_locations(self):
        from location.models import Model as Location

        l1 = Location.objects.create(name="Berlin", country="DE")
        l2 = Location.objects.create(name="Hamburg", country="DE")
        response = self.client.post(
            reverse("location:bulk_delete"),
            {"selected_ids": [l1.pk, l2.pk]},
        )
        self.assertRedirects(response, reverse("location:index"))
        self.assertFalse(Location.objects.filter(pk__in=[l1.pk, l2.pk]).exists())

    def test_bulk_delete_statuses(self):
        from status.models import Model as Status

        s1 = Status.objects.create(name="Bulk Active")
        s2 = Status.objects.create(name="Bulk Retired")
        response = self.client.post(
            reverse("status:bulk_delete"),
            {"selected_ids": [s1.pk, s2.pk]},
        )
        self.assertRedirects(response, reverse("status:index"))
        self.assertFalse(Status.objects.filter(pk__in=[s1.pk, s2.pk]).exists())

    def test_bulk_delete_patchtimes(self):
        from patchtime.models import Model as Patchtime

        p1 = Patchtime.objects.create(name="Sunday 2am")
        p2 = Patchtime.objects.create(name="Saturday 11pm")
        response = self.client.post(
            reverse("patchtime:bulk_delete"),
            {"selected_ids": [p1.pk, p2.pk]},
        )
        self.assertRedirects(response, reverse("patchtime:index"))
        self.assertFalse(Patchtime.objects.filter(pk__in=[p1.pk, p2.pk]).exists())

    def test_bulk_delete_requires_delete_permission(self):
        from vendor.models import Model as Vendor
        from django.contrib.auth.models import User

        user = User.objects.create_user("novendorperm", password=PASSWORD)
        # Drop the auto-created personal workspace (which grants full perms)
        # so this user genuinely lacks the delete permission.
        user.groups.clear()
        self.client.logout()
        self.client.force_login(user)
        v1 = Vendor.objects.create(name="Protected Vendor")
        response = self.client.post(
            reverse("vendor:bulk_delete"), {"selected_ids": [v1.pk]}
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Vendor.objects.filter(pk=v1.pk).exists())

    def test_bulk_delete_no_selection(self):
        response = self.client.post(reverse("vendor:bulk_delete"), {"selected_ids": []})
        self.assertRedirects(response, reverse("vendor:index"))


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ServerBulkActionTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Server Group")
        self.superuser = User.objects.create_superuser("srvsuper", "s@e.c", PASSWORD)
        self.client.force_login(self.superuser)
        from status.models import Model as Status
        from domain.models import Model as Domain
        from server.models import Model as Server

        self.status = Status.objects.create(name="In use")
        self.retired = Status.objects.create(name="Retired")
        self.domain = Domain.objects.create(name="srv.example.com")
        self.server = Server.objects.create(
            hostname="bulk01", status=self.status, domain=self.domain
        )

    def test_bulk_status_change(self):
        response = self.client.post(
            reverse("server:bulk_action"),
            {"selected_ids": [self.server.pk], "status": self.retired.pk},
        )
        self.assertRedirects(response, reverse("server:index"))
        self.server.refresh_from_db()
        self.assertEqual(self.server.status, self.retired)

    def test_bulk_delete(self):
        response = self.client.post(
            reverse("server:bulk_action"),
            {"selected_ids": [self.server.pk], "delete": "on"},
        )
        self.assertRedirects(response, reverse("server:index"))
        from server.models import Model as Server

        self.assertFalse(Server.objects.filter(pk=self.server.pk).exists())

    def test_bulk_no_selection(self):
        response = self.client.post(reverse("server:bulk_action"), {"selected_ids": []})
        self.assertRedirects(response, reverse("server:index"))


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class AuditLogTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Audit Group")
        self.other_group = Group.objects.create(name="Other Group")
        self.superuser = User.objects.create_superuser("audituser", "a@e.c", PASSWORD)
        self.client.force_login(self.superuser)
        from vendor.models import Model as Vendor

        Vendor.objects.create(name="Audited Vendor", group=self.group)
        Vendor.objects.create(name="Other Vendor", group=self.other_group)

    def test_audit_log_lists_entries(self):
        response = self.client.get(reverse("audit_log"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audited Vendor")
        self.assertContains(response, "Other Vendor")

    def test_audit_log_group_filter(self):
        response = self.client.get(reverse("audit_log") + f"?group={self.group.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audited Vendor")
        self.assertNotContains(response, "Other Vendor")

    def test_audit_log_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("audit_log"))
        self.assertEqual(response.status_code, 302)

    def test_audit_log_partitioned_for_regular_user(self):
        from django.contrib.auth.models import User

        user = User.objects.create_user("auditmember", password=PASSWORD)
        user.groups.add(self.group)
        self.client.logout()
        self.client.force_login(user)
        response = self.client.get(reverse("audit_log"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audited Vendor")
        self.assertNotContains(response, "Other Vendor")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class OnboardingFlowTest(TestCase):
    def test_user_with_only_workspace_needs_onboarding(self):
        user = User.objects.create_user("newbie", password=PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertTrue(response.context["ONBOARDING_NEEDED"])

    def test_user_with_real_group_no_onboarding(self):
        group = Group.objects.create(name="Real Team")
        user = User.objects.create_user("member", password=PASSWORD)
        user.groups.add(group)
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertFalse(response.context["ONBOARDING_NEEDED"])

    def test_onboarding_page(self):
        user = User.objects.create_user("onboarding", password=PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("group_onboarding"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to ServerManager")

    def test_onboarding_join_with_invalid_token(self):
        user = User.objects.create_user("joiner", password=PASSWORD)
        self.client.force_login(user)
        response = self.client.post(
            reverse("group_onboarding"), {"action": "join", "token": "not-a-uuid"}
        )
        self.assertEqual(response.status_code, 200)

    def test_onboarding_create_redirects(self):
        user = User.objects.create_user("creator2", password=PASSWORD)
        self.client.force_login(user)
        response = self.client.post(reverse("group_onboarding"), {"action": "create"})
        self.assertEqual(response.status_code, 302)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class TagsFeatureTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Tag Group")
        self.user = User.objects.create_user("taguser", password=PASSWORD)
        self.user.groups.add(self.group)
        self.client.force_login(self.user)
        from vendor.models import Model as Vendor

        self.vendor = Vendor.objects.create(name="Tag Vendor", group=self.group)

    def test_vendor_tags_assignable_and_listed(self):
        self.vendor.tags.add("prod", "db")
        self.assertEqual(list(self.vendor.tags.names()), ["prod", "db"])
        response = self.client.get(reverse("vendor:detail", args=[self.vendor.pk]))
        self.assertContains(response, "prod")

    def test_server_has_tags_field(self):
        from server.models import Model as Server
        from status.models import Model as Status
        from domain.models import Model as Domain

        status = Status.objects.create(name="Active", group=self.group)
        domain = Domain.objects.create(name="t.example.com", group=self.group)
        server = Server.objects.create(
            hostname="tagged01", status=status, domain=domain, group=self.group
        )
        server.tags.add("critical")
        self.assertEqual(list(server.tags.names()), ["critical"])


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class TenantConstraintFixTest(TestCase):
    """
    Regression tests for the multi-tenancy constraint fixes: two groups must
    be able to hold items with identical natural keys.
    """

    def setUp(self):
        self.group_a = Group.objects.create(name="Fix Group A")
        self.group_b = Group.objects.create(name="Fix Group B")
        from domain.models import Model as Domain
        from status.models import Model as Status

        self.status = Status.objects.create(name="Active")
        self.domain = Domain.objects.create(name="fix.example.com")

    def test_same_hostname_across_groups(self):
        from server.models import Model as Server

        Server.objects.create(
            hostname="shared01",
            status=self.status,
            domain=self.domain,
            group=self.group_a,
        )
        Server.objects.create(
            hostname="shared01",
            status=self.status,
            domain=self.domain,
            group=self.group_b,
        )
        self.assertEqual(Server.objects.filter(hostname="shared01").count(), 2)

    def test_same_cluster_name_across_groups(self):
        from cluster.models import Model as Cluster

        Cluster.objects.create(name="SharedCluster", group=self.group_a)
        Cluster.objects.create(name="SharedCluster", group=self.group_b)
        self.assertEqual(Cluster.objects.filter(name="SharedCluster").count(), 2)

    def test_same_domain_name_across_groups(self):
        from domain.models import Model as Domain

        Domain.objects.create(name="dup.example.com", group=self.group_a)
        Domain.objects.create(name="dup.example.com", group=self.group_b)
        self.assertEqual(Domain.objects.filter(name="dup.example.com").count(), 2)

    def test_same_clustersoftware_across_groups(self):
        from vendor.models import Model as Vendor
        from clustersoftware.models import Model as ClusterSoftware

        vendor = Vendor.objects.create(name="Fix Vendor")
        ClusterSoftware.objects.create(
            name="Postgres", version="17", vendor=vendor, group=self.group_a
        )
        ClusterSoftware.objects.create(
            name="Postgres", version="17", vendor=vendor, group=self.group_b
        )
        self.assertEqual(ClusterSoftware.objects.filter(name="Postgres").count(), 2)

    def test_same_servermodel_across_groups(self):
        from vendor.models import Model as Vendor
        from servermodel.models import Model as ServerModel

        vendor = Vendor.objects.create(name="Fix Vendor 2")
        ServerModel.objects.create(name="R740", vendor=vendor, group=self.group_a)
        ServerModel.objects.create(name="R740", vendor=vendor, group=self.group_b)
        self.assertEqual(ServerModel.objects.filter(name="R740").count(), 2)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class GroupPermissionAllModelsTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Perm All Group")
        self.owner = User.objects.create_user("permall", password=PASSWORD)
        self.group.profile.owner = self.owner
        self.group.profile.save()
        self.group.user_set.add(self.owner)
        self.client.login(username="permall", password=PASSWORD)

    def test_group_permission_form_has_all_models(self):
        from .utils_permissions import APP_MODELS

        response = self.client.get(
            reverse("group_permission_edit", args=[self.group.pk])
        )
        self.assertEqual(response.status_code, 200)
        for app_label, _ in APP_MODELS:
            self.assertContains(response, f'name="edit_{app_label}"')


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class DuplicateGlobalItemsTest(TestCase):
    """
    Regression: the DB UniqueConstraint(name, group) allows multiple NULL-group
    rows with the same name, so global duplicates must be blocked at the form
    level and made visible in the list UI.
    """

    def setUp(self):
        self.group = Group.objects.create(name="Dup Group")
        self.superuser = User.objects.create_superuser("dupsuper", "s@e.c", PASSWORD)
        self.client.force_login(self.superuser)
        from status.models import Model as Status

        Status.objects.create(name="In use")

    def test_global_status_duplicate_blocked(self):
        from status.models import Model as Status

        response = self.client.post(reverse("status:create"), {"name": "In use"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Status.objects.filter(name="In use").count(), 1)

    def test_group_status_same_name_allowed(self):
        """
        A group member creating a status auto-assigns their group, so the same
        name is allowed alongside the global one.
        """
        from status.models import Model as Status
        from django.contrib.auth.models import User
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        user = User.objects.create_user("statusmember", password=PASSWORD)
        ct = ContentType.objects.get(app_label="status", model="model")
        self.group.permissions.add(*Permission.objects.filter(content_type=ct))
        user.groups.add(self.group)
        self.client.logout()
        self.client.force_login(user)
        response = self.client.post(reverse("status:create"), {"name": "In use"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Status.objects.filter(name="In use").count(), 2)
        self.assertEqual(
            Status.objects.get(name="In use", group=self.group).group,
            self.group,
        )

    def test_status_list_shows_group_badge(self):
        from status.models import Model as Status

        Status.objects.create(name="Group Only", group=self.group)
        response = self.client.get(reverse("status:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Global")
        self.assertContains(response, "Dup Group")

    def test_location_list_shows_group_badge(self):
        from location.models import Model as Location

        Location.objects.create(name="Berlin", country="DE")
        Location.objects.create(name="Hamburg", country="DE", group=self.group)
        response = self.client.get(reverse("location:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Global")
        self.assertContains(response, "Dup Group")
