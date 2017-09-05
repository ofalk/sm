from __future__ import unicode_literals

from django import forms

from . models import Status


class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = '__all__'


class StatusFormDisabled(StatusForm):
    def __init__(self, *args, **kwargs):
        super(StatusFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
