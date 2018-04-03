from __future__ import unicode_literals

from . models import Model
from sm.forms import SMForm, SMFormDisabled


class Form(SMForm):
    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
