from __future__ import unicode_literals

from django import forms

from . models import Model
from server.models import Server as ServerModel


class Form(forms.ModelForm):
    server_set = forms.ModelMultipleChoiceField(
        label='Server',
        queryset=ServerModel.objects.all().order_by('-cluster', 'hostname')
    )

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)

        self.fields['server_set'].initial = (
            self.instance.server_set.all().values_list('id', flat=True)
        )

    class Meta:
        model = Model
        fields = '__all__'


class FormDisabled(Form):
    def __init__(self, *args, **kwargs):
        super(FormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
