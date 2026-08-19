from .models import Model
from sm.forms import SMForm, SMFormDisabled
from sm.mixins import filter_queryset_for_user
from vendor.models import Model as VendorModel


class Form(SMForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = filter_queryset_for_user(
            VendorModel.objects.filter(is_hardware=True), self.user
        )

    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
