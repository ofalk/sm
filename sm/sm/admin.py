from django.contrib import admin

from patchtime.models import Patchtime
from server.models import Server
from status.models import Status
from domain.models import Domain
from location.models import Model as LocationModel
from vendor.models import Vendor
from operatingsystem.models import Operatingsystem

admin.site.register(Patchtime)
admin.site.register(Server)
admin.site.register(Status)
admin.site.register(Domain)
admin.site.register(LocationModel)
admin.site.register(Vendor)
admin.site.register(Operatingsystem)
