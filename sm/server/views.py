from __future__ import unicode_literals

from django.views.generic import ListView
from account.mixins import LoginRequiredMixin

from . models import Server


class ServerView(LoginRequiredMixin, ListView):
    template_name = 'server/list.html'
    model = Server
    paginate_by = 20
    queryset = model.objects.all()
    orphans = 3
    ordering = '-id'
