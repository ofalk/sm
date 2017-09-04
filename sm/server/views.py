from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Server

from django import forms

from django.views.generic.edit import UpdateView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from django.utils.translation import ugettext as _

from django.core.urlresolvers import reverse_lazy


class ServerListView(LoginRequiredMixin, ListView, SuccessMessageMixin):
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


class ServerFormDisabled(ServerForm):
    def __init__(self, *args, **kwargs):
        super(ServerFormDisabled, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True


class ServerDetailView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
    template_name = 'server/detail.html'
    model = Server
    form_class = ServerFormDisabled


class ServerUpdateView(ServerDetailView, SuccessMessageMixin):
    template_name = 'server/edit.html'
    form_class = ServerForm


class ServerCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    template_name = 'server/edit.html'
    form_class = ServerForm
    model = Server
    success_url = reverse_lazy('server:index')

    def get_success_url(self):
        messages.add_message(self.request, messages.INFO, 'Hello world.')
        return self.success_url

    def get_succes_message(self, cleaned_data):
        return _('Server successfully created')


class ServerSearchView(LoginRequiredMixin, ListView):
    template_name = 'server/list.html'
    model = Server
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = 'hostname'
