from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Server

from django import forms

from django.views.generic.edit import UpdateView, CreateView


class ServerListView(LoginRequiredMixin, ListView):
    template_name = 'server/list.html'
    model = Server
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'hostname'


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = '__all__'
        widgets = {
            'delivery_date': forms.DateInput(attrs={'class': 'date-input'}),
            'install_date': forms.DateInput(attrs={'class': 'date-input'})
        }


class ServerDetailView(UpdateView):
    template_name = 'server/detail.html'
    form_class = ServerForm
    model = Server


class ServerCreateView(CreateView):
    template_name = 'server/detail.html'
    form_class = ServerForm
    model = Server
