from rest_framework import serializers
from vendor.models import Model as Vendor
from status.models import Model as Status
from location.models import Model as Location
from domain.models import Model as Domain
from patchtime.models import Model as Patchtime
from operatingsystem.models import Model as OS
from servermodel.models import Model as ServerModel
from server.models import Model as Server

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'is_hardware', 'is_software']

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'name']

class OSSerializer(serializers.ModelSerializer):
    vendor = serializers.SlugRelatedField(slug_field='name', queryset=Vendor.objects.all())
    class Meta:
        model = OS
        fields = ['id', 'version', 'vendor']

class ServerModelSerializer(serializers.ModelSerializer):
    vendor = serializers.SlugRelatedField(slug_field='name', queryset=Vendor.objects.all())
    class Meta:
        model = ServerModel
        fields = ['id', 'name', 'vendor']

class ServerSerializer(serializers.ModelSerializer):
    status = serializers.SlugRelatedField(slug_field='name', queryset=Status.objects.all())
    domain = serializers.SlugRelatedField(slug_field='name', queryset=Domain.objects.all())
    location = serializers.SlugRelatedField(slug_field='name', queryset=Location.objects.all())
    patchtime = serializers.SlugRelatedField(slug_field='name', queryset=Patchtime.objects.all())
    operatingsystem = OSSerializer(read_only=True)
    servermodel = ServerModelSerializer(read_only=True)

    class Meta:
        model = Server
        fields = [
            'id', 'hostname', 'domain', 'status', 'location', 
            'operatingsystem', 'servermodel', 'patchtime', 
            'primary_ip', 'delivery_date', 'install_date', 'description'
        ]
