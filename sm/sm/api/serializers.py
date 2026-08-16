from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from taggit.serializers import TaggitSerializer, TagListSerializerField
from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from domain.models import Model as Domain
from patchtime.models import Model as Patchtime
from operatingsystem.models import Model as OS
from servermodel.models import Model as ServerModel
from server.models import Model as Server
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from clustersoftware.models import Model as ClusterSoftware
from clusterpackagetype.models import Model as ClusterPackageType

from sm.mixins import filter_queryset_by_tenant


class TenantSlugRelatedField(serializers.SlugRelatedField):
    """
    A ``SlugRelatedField`` whose queryset is scoped to the requesting user's
    accessible groups, so a user can never reference (create/update against) a
    related object belonging to another tenant.
    """

    def get_queryset(self):
        request = self.context.get("request")
        if request is not None and not getattr(request.user, "is_superuser", False):
            return filter_queryset_by_tenant(self.queryset, request)
        return self.queryset


class TenantPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """A PK related field scoped to the requesting user's accessible groups."""

    def get_queryset(self):
        request = self.context.get("request")
        if request is not None and not getattr(request.user, "is_superuser", False):
            return filter_queryset_by_tenant(self.queryset, request)
        return self.queryset


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ["id", "name", "is_hardware", "is_software"]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["id", "name"]


class OSSerializer(serializers.ModelSerializer):
    vendor = TenantSlugRelatedField(slug_field="name", queryset=Vendor.objects.all())

    class Meta:
        model = OS
        fields = ["id", "version", "vendor"]


class ServerModelSerializer(serializers.ModelSerializer):
    vendor = TenantSlugRelatedField(slug_field="name", queryset=Vendor.objects.all())

    class Meta:
        model = ServerModel
        fields = ["id", "name", "vendor"]


class CoercingDateField(serializers.DateField):
    """
    Date field that tolerates datetime values. The server model stores
    ``default=timezone.now`` for its DateFields, which can yield datetimes.
    """

    def to_representation(self, value):
        if isinstance(value, datetime):
            value = value.date()
        return super().to_representation(value)


class ServerSerializer(TaggitSerializer, serializers.ModelSerializer):
    status = TenantSlugRelatedField(slug_field="name", queryset=Status.objects.all())
    domain = TenantSlugRelatedField(slug_field="name", queryset=Domain.objects.all())
    location = TenantSlugRelatedField(
        slug_field="name",
        queryset=Location.objects.all(),
        required=False,
        allow_null=True,
    )
    patchtime = TenantSlugRelatedField(
        slug_field="name",
        queryset=Patchtime.objects.all(),
        required=False,
        allow_null=True,
    )
    operatingsystem = OSSerializer(read_only=True)
    servermodel = ServerModelSerializer(read_only=True)
    delivery_date = CoercingDateField(required=False)
    install_date = CoercingDateField(required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Server
        fields = [
            "id",
            "hostname",
            "domain",
            "status",
            "location",
            "operatingsystem",
            "servermodel",
            "patchtime",
            "primary_ip",
            "delivery_date",
            "install_date",
            "description",
            "application",
            "rack",
            "monitoring_from_puppet",
            "management_ip",
            "management_hostname",
            "tags",
        ]


class LocationSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Location
        fields = "__all__"


class DomainSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Domain
        fields = "__all__"


class PatchtimeSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Patchtime
        fields = "__all__"


class ClusterSerializer(TaggitSerializer, serializers.ModelSerializer):
    clustersoftware = TenantPrimaryKeyRelatedField(
        queryset=ClusterSoftware.objects.all(),
        required=False,
        allow_null=True,
    )
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Cluster
        fields = "__all__"


class ClusterPackageSerializer(TaggitSerializer, serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    package_type_name = serializers.CharField(
        source="package_type.name", read_only=True
    )
    cluster_name = serializers.CharField(source="cluster.name", read_only=True)
    clustersoftware = serializers.CharField(
        source="cluster.clustersoftware.name", read_only=True, allow_null=True
    )
    clustersoftwareversion = serializers.CharField(
        source="cluster.clustersoftware.version", read_only=True, allow_null=True
    )
    cluster = TenantPrimaryKeyRelatedField(queryset=Cluster.objects.all())
    status = TenantPrimaryKeyRelatedField(queryset=Status.objects.all())
    package_type = TenantPrimaryKeyRelatedField(
        queryset=ClusterPackageType.objects.all()
    )
    tags = TagListSerializerField(required=False)

    class Meta:
        model = ClusterPackage
        fields = "__all__"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        cluster = attrs.get("cluster", getattr(self.instance, "cluster", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        status = attrs.get("status", getattr(self.instance, "status", None))
        package_type = attrs.get(
            "package_type", getattr(self.instance, "package_type", None)
        )
        if None in (cluster, name, status, package_type):
            return attrs
        request = self.context.get("request")
        group = None
        if request and request.user and not request.user.is_superuser:
            group = request.user.groups.first()
        qs = ClusterPackage.objects.filter(
            cluster=cluster,
            name=name,
            status=status,
            package_type=package_type,
            group=group,
        )
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                _(
                    "A cluster package with this cluster, name, status and "
                    "package type already exists."
                )
            )
        return attrs


class ClusterSoftwareSerializer(serializers.ModelSerializer):
    vendor = TenantSlugRelatedField(slug_field="name", queryset=Vendor.objects.all())

    class Meta:
        model = ClusterSoftware
        fields = ["id", "name", "version", "vendor"]


class ClusterPackageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClusterPackageType
        fields = ["id", "name"]
