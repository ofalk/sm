from __future__ import unicode_literals

from django import forms

from . models import Domain


class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = '__all__'


class DomainFormDisabled(DomainForm):
    def __init__(self, *args, **kwargs):
        super(DomainFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
