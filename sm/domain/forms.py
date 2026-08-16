from .models import Model
from sm.forms import SMForm, SMFormDisabled, UniquePerGroupMixin


class Form(UniquePerGroupMixin, SMForm):
    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
