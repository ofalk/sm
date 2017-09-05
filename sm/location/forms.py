from __future__ import unicode_literals

from django import forms

from . models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'


class LocationFormDisabled(LocationForm):
    def __init__(self, *args, **kwargs):
        super(LocationFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
