from rest_framework import viewsets, permissions
from server.models import Model as Server
from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from domain.models import Model as Domain
from patchtime.models import Model as Patchtime
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage

from sm.mixins import APIMultiTenantMixin

from .serializers import (
    ServerSerializer,
    VendorSerializer,
    StatusSerializer,
    LocationSerializer,
    DomainSerializer,
    PatchtimeSerializer,
    ClusterSerializer,
    ClusterPackageSerializer,
)


class ServerViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows servers to be viewed or edited.
    """

    queryset = Server.objects.all().order_by("hostname")
    serializer_class = ServerSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class VendorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vendors to be viewed or edited.
    """

    queryset = Vendor.objects.all().order_by("name")
    serializer_class = VendorSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows statuses to be viewed or edited.
    """

    queryset = Status.objects.all().order_by("name")
    serializer_class = StatusSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class DomainViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by("name")
    serializer_class = DomainSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class PatchtimeViewSet(viewsets.ModelViewSet):
    queryset = Patchtime.objects.all().order_by("name")
    serializer_class = PatchtimeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class ClusterViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = Cluster.objects.all().order_by("name")
    serializer_class = ClusterSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class ClusterPackageViewSet(viewsets.ModelViewSet):
    # ClusterPackage is linked to Cluster (MultiTenant)
    queryset = ClusterPackage.objects.all().order_by("name")
    serializer_class = ClusterPackageSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups)
