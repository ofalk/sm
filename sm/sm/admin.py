from django.contrib import admin

from patchtime.models import Model as PatchtimeModel
from server.models import Server as ServerModel
from servermodel.models import Model as ServermodelModel
from status.models import Model as StatusModel
from domain.models import Model as DomainModel
from location.models import Model as LocationModel
from vendor.models import Model as VendorModel
from operatingsystem.models import Operatingsystem as OperatingsystemModel

admin.site.register(PatchtimeModel)
admin.site.register(ServerModel)
admin.site.register(ServermodelModel)
admin.site.register(StatusModel)
admin.site.register(DomainModel)
admin.site.register(LocationModel)
admin.site.register(VendorModel)
admin.site.register(OperatingsystemModel)
