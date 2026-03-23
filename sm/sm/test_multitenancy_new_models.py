from django.test import TestCase
from django.contrib.auth.models import Group

from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from patchtime.models import Model as Patchtime
from servermodel.models import Model as ServerModel
from clustersoftware.models import Model as ClusterSoftware
from clusterpackagetype.models import Model as ClusterPackageType
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from .mixins import get_tenant_model_counts


class NewTenantModelsPartitioningTest(TestCase):
    """Test that newly multi-tenancy-enabled models are partitioned by group."""

    def setUp(self) -> None:
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        self.vendor_a = Vendor.objects.create(name="Vendor A", group=self.group_a)
        self.vendor_b = Vendor.objects.create(name="Vendor B", group=self.group_b)

    def test_status_same_name_in_different_groups(self) -> None:
        Status.objects.create(name="active", group=self.group_a)
        Status.objects.create(name="active", group=self.group_b)
        self.assertEqual(Status.objects.filter(name="active").count(), 2)

    def test_patchtime_same_name_in_different_groups(self) -> None:
        Patchtime.objects.create(name="Sunday 2am", group=self.group_a)
        Patchtime.objects.create(name="Sunday 2am", group=self.group_b)
        self.assertEqual(Patchtime.objects.filter(name="Sunday 2am").count(), 2)

    def test_location_same_name_in_different_groups(self) -> None:
        Location.objects.create(name="Berlin", country="DE", group=self.group_a)
        Location.objects.create(name="Berlin", country="DE", group=self.group_b)
        self.assertEqual(Location.objects.filter(name="Berlin").count(), 2)

    def test_clusterpackagetype_same_name_in_different_groups(self) -> None:
        ClusterPackageType.objects.create(name="helm", group=self.group_a)
        ClusterPackageType.objects.create(name="helm", group=self.group_b)
        self.assertEqual(ClusterPackageType.objects.filter(name="helm").count(), 2)

    def test_servermodel_same_name_in_different_groups(self) -> None:
        ServerModel.objects.create(
            name="PowerEdge R640", vendor=self.vendor_a, group=self.group_a
        )
        ServerModel.objects.create(
            name="PowerEdge R640", vendor=self.vendor_b, group=self.group_b
        )
        self.assertEqual(ServerModel.objects.filter(name="PowerEdge R640").count(), 2)

    def test_clustersoftware_same_name_in_different_groups(self) -> None:
        ClusterSoftware.objects.create(
            name="k3s", version="1.0", vendor=self.vendor_a, group=self.group_a
        )
        ClusterSoftware.objects.create(
            name="k3s", version="1.0", vendor=self.vendor_b, group=self.group_b
        )
        self.assertEqual(ClusterSoftware.objects.filter(name="k3s").count(), 2)

    def test_clusterpackage_same_name_in_different_groups(self) -> None:
        cs_a = ClusterSoftware.objects.create(
            name="k3s", version="1.0", vendor=self.vendor_a, group=self.group_a
        )
        cs_b = ClusterSoftware.objects.create(
            name="k3s", version="1.0", vendor=self.vendor_b, group=self.group_b
        )
        cluster_a = Cluster.objects.create(
            name="cluster-a", clustersoftware=cs_a, group=self.group_a
        )
        cluster_b = Cluster.objects.create(
            name="cluster-b", clustersoftware=cs_b, group=self.group_b
        )
        status_a = Status.objects.create(name="active", group=self.group_a)
        status_b = Status.objects.create(name="active", group=self.group_b)
        cpt_a = ClusterPackageType.objects.create(name="helm", group=self.group_a)
        cpt_b = ClusterPackageType.objects.create(name="helm", group=self.group_b)

        ClusterPackage.objects.create(
            name="my-app",
            cluster=cluster_a,
            status=status_a,
            package_type=cpt_a,
            description="desc",
            host="10.0.0.1",
            group=self.group_a,
        )
        ClusterPackage.objects.create(
            name="my-app",
            cluster=cluster_b,
            status=status_b,
            package_type=cpt_b,
            description="desc",
            host="10.0.0.2",
            group=self.group_b,
        )
        self.assertEqual(ClusterPackage.objects.filter(name="my-app").count(), 2)


class QuotaCountingTest(TestCase):
    """Test that quota counting includes all newly tenant-aware models."""

    def setUp(self) -> None:
        self.group = Group.objects.create(name="Test Group")
        self.vendor = Vendor.objects.create(name="Test Vendor", group=self.group)

    def test_status_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        Status.objects.create(name="active", group=self.group)
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_patchtime_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        Patchtime.objects.create(name="Sunday 2am", group=self.group)
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_location_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        Location.objects.create(name="Berlin", country="DE", group=self.group)
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_clusterpackagetype_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        ClusterPackageType.objects.create(name="helm", group=self.group)
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_servermodel_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        ServerModel.objects.create(
            name="PowerEdge R640", vendor=self.vendor, group=self.group
        )
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_clustersoftware_counted_in_quota(self) -> None:
        count_before = get_tenant_model_counts(self.group)
        ClusterSoftware.objects.create(
            name="k3s", version="1.0", vendor=self.vendor, group=self.group
        )
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_after, count_before + 1)

    def test_quota_not_counted_for_other_group(self) -> None:
        other_group = Group.objects.create(name="Other Group")
        count_before = get_tenant_model_counts(self.group)
        Status.objects.create(name="active", group=other_group)
        count_after = get_tenant_model_counts(self.group)
        self.assertEqual(count_before, count_after)

    def test_quota_not_counted_for_no_group(self) -> None:
        self.assertEqual(get_tenant_model_counts(None), 0)
