from django.contrib import admin

from patchtime.models import Patchtime as PatchtimeModel
from server.models import Server as ServerModel
from servermodel.models import Servermodel as ServermodelModel
from status.models import Status as StatusModel
from domain.models import Model as DomainModel
from location.models import Model as LocationModel
from vendor.models import Vendor as VendorModel
from operatingsystem.models import Operatingsystem as OperatingsystemModel

admin.site.register(PatchtimeModel)
admin.site.register(ServerModel)
admin.site.register(ServermodelModel)
admin.site.register(StatusModel)
admin.site.register(DomainModel)
admin.site.register(LocationModel)
admin.site.register(VendorModel)
admin.site.register(OperatingsystemModel)
