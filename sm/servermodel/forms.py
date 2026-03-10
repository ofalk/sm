from __future__ import unicode_literals

from . models import Model
from sm.forms import SMForm, SMFormDisabled
from vendor.models import Model as VendorModel


class Form(SMForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = VendorModel.objects.filter(is_hardware=True)

    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
