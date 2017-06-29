from django.contrib import admin

from location.models import *
from patchtime.models import *
from server.models import *
from status.models import *
from vendor.models import *
from operatingsystem.models import *

admin.site.register(Patchtime)
admin.site.register(Server)
admin.site.register(Status)
admin.site.register(Location)
admin.site.register(Vendor)
admin.site.register(Operatingsystem)
