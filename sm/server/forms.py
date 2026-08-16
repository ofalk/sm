from .models import Model as ServerModel
from sm.forms import SMForm, SMFormDisabled
from status.models import Model as StatusModel

from django.forms import DateInput
from django import forms


class Form(SMForm):
    """
    Override default form behaviour; Make sure 'In Use' is the default/initial
    value
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_status = StatusModel.objects.filter(name="In use").first()
            if default_status:
                self.fields["status"].initial = default_status.id
        except Exception as e:  # noqa # flake8: noqa # NOQA # pragma: no cover
            print('No status "In Use" found: %s' % e)

    class Meta(SMForm.Meta):
        model = ServerModel
        widgets = {
            "delivery_date": DateInput(attrs={"class": "date-input"}),
            "install_date": DateInput(attrs={"class": "date-input"}),
        }


class FormDisabled(Form, SMFormDisabled):
    pass


class BulkActionForm(forms.Form):
    status = forms.ModelChoiceField(
        queryset=StatusModel.objects.all(),
        required=False,
        label="Change Status to",
        empty_label="--- No Change ---",
    )
    delete = forms.BooleanField(required=False, label="Delete Selected Servers")
    decommission = forms.BooleanField(
        required=False, label="Decommission (set decommission date)"
    )
