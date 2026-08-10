from rest_framework import viewsets
from server.models import Model as Server
from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from domain.models import Model as Domain
from patchtime.models import Model as Patchtime
from operatingsystem.models import Model as OS
from servermodel.models import Model as ServerModel
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from clustersoftware.models import Model as ClusterSoftware
from clusterpackagetype.models import Model as ClusterPackageType

from sm.mixins import APIMultiTenantMixin
from sm.api.permissions import SmModelPermissions

from .serializers import (
    ServerSerializer,
    VendorSerializer,
    StatusSerializer,
    LocationSerializer,
    DomainSerializer,
    PatchtimeSerializer,
    OSSerializer,
    ServerModelSerializer,
    ClusterSerializer,
    ClusterPackageSerializer,
    ClusterSoftwareSerializer,
    ClusterPackageTypeSerializer,
)


class ServerViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows servers to be viewed or edited.
    """

    queryset = Server.objects.all().order_by("hostname")
    serializer_class = ServerSerializer
    permission_classes = [SmModelPermissions]


class VendorViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows vendors to be viewed or edited.
    """

    queryset = Vendor.objects.all().order_by("name")
    serializer_class = VendorSerializer
    permission_classes = [SmModelPermissions]


class StatusViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows statuses to be viewed or edited.
    """

    queryset = Status.objects.all().order_by("name")
    serializer_class = StatusSerializer
    permission_classes = [SmModelPermissions]


class LocationViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [SmModelPermissions]


class DomainViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by("name")
    serializer_class = DomainSerializer
    permission_classes = [SmModelPermissions]


class PatchtimeViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Patchtime.objects.all().order_by("name")
    serializer_class = PatchtimeSerializer
    permission_classes = [SmModelPermissions]


class OSViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = OS.objects.all().order_by("version")
    serializer_class = OSSerializer
    permission_classes = [SmModelPermissions]


class ServerModelViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = ServerModel.objects.all().order_by("name")
    serializer_class = ServerModelSerializer
    permission_classes = [SmModelPermissions]


class ClusterViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Cluster.objects.all().order_by("name")
    serializer_class = ClusterSerializer
    permission_classes = [SmModelPermissions]


class ClusterPackageViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = ClusterPackage.objects.all().order_by("name")
    serializer_class = ClusterPackageSerializer
    permission_classes = [SmModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups)


class ClusterSoftwareViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = ClusterSoftware.objects.all().order_by("name")
    serializer_class = ClusterSoftwareSerializer
    permission_classes = [SmModelPermissions]


class ClusterPackageTypeViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = ClusterPackageType.objects.all().order_by("name")
    serializer_class = ClusterPackageTypeSerializer
    permission_classes = [SmModelPermissions]
