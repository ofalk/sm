from rest_framework import viewsets, permissions
from server.models import Model as Server
from vendor.models import Model as Vendor
from status.models import Model as Status
from .serializers import ServerSerializer, VendorSerializer, StatusSerializer

class ServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows servers to be viewed or edited.
    """
    queryset = Server.objects.all().order_by('hostname')
    serializer_class = ServerSerializer
    permission_classes = [permissions.IsAuthenticated]

class VendorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vendors to be viewed or edited.
    """
    queryset = Vendor.objects.all().order_by('name')
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

class StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows statuses to be viewed or edited.
    """
    queryset = Status.objects.all().order_by('name')
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated]
