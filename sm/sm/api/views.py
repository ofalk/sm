from rest_framework import viewsets, permissions
from server.models import Model as Server
from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from domain.models import Model as Domain
from patchtime.models import Model as Patchtime
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage

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


class ServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows servers to be viewed or edited.
    """

    queryset = Server.objects.all().order_by("hostname")
    serializer_class = ServerSerializer
    permission_classes = [permissions.IsAuthenticated]


class VendorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vendors to be viewed or edited.
    """

    queryset = Vendor.objects.all().order_by("name")
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]


class StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows statuses to be viewed or edited.
    """

    queryset = Status.objects.all().order_by("name")
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by("name")
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]


class PatchtimeViewSet(viewsets.ModelViewSet):
    queryset = Patchtime.objects.all().order_by("name")
    serializer_class = PatchtimeSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all().order_by("name")
    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClusterPackageViewSet(viewsets.ModelViewSet):
    queryset = ClusterPackage.objects.all().order_by("name")
    serializer_class = ClusterPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
