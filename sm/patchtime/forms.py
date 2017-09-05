from __future__ import unicode_literals

from django import forms

from . models import Patchtime


class PatchtimeForm(forms.ModelForm):
    class Meta:
        model = Patchtime
        fields = '__all__'


class PatchtimeFormDisabled(PatchtimeForm):
    def __init__(self, *args, **kwargs):
        super(PatchtimeFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
