from __future__ import unicode_literals

from . models import Server

from django import forms


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = '__all__'
        widgets = {
            'delivery_date': forms.DateInput(attrs={'class': 'date-input'}),
            'install_date': forms.DateInput(attrs={'class': 'date-input'})
        }


class ServerFormDisabled(ServerForm):
    def __init__(self, *args, **kwargs):
        super(ServerFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
