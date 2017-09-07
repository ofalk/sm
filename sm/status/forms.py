from __future__ import unicode_literals

from django import forms

from . models import Model


class Form(forms.ModelForm):
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
