from __future__ import unicode_literals

from . models import Model as ServerModel
from sm.forms import SMForm, SMFormDisabled
from status.models import Model as StatusModel

from django.forms import DateInput


class Form(SMForm):
    """
    Override default form behaviour; Make sure 'In Use' is the default/initial
    value
    """
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        try:
            self.fields['status'].initial = StatusModel.objects.get(
                name='In use').id
        except Exception as e:  # noqa # flake8: noqa # NOQA # pragma: no cover
            print('No status "In Use" found: %s' % e)

    class Meta(SMForm.Meta):
        model = ServerModel
        widgets = {
            'delivery_date': DateInput(attrs={'class': 'date-input'}),
            'install_date': DateInput(attrs={'class': 'date-input'})
        }


class FormDisabled(Form, SMFormDisabled):
    pass
