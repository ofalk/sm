from __future__ import unicode_literals

from . models import Model as ServerModel
from status.models import Model as StatusModel

from django import forms


class Form(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self.fields['status'].initial = StatusModel.objects.get(
            name='In use').id

    class Meta:
        model = ServerModel
        fields = '__all__'
        widgets = {
            'delivery_date': forms.DateInput(attrs={'class': 'date-input'}),
            'install_date': forms.DateInput(attrs={'class': 'date-input'})
        }


class FormDisabled(Form):
    def __init__(self, *args, **kwargs):
        super(FormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
