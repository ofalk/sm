from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Model
from .forms import Form
from .forms import FormDisabled
from . import app_label

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView

from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

try:
    from django.urls import reverse_lazy
except Exception as e:  # pragma: no cover
    from django.urls import reverse_lazy  # pragma: no cover

from django.contrib import messages


class ListView(LoginRequiredMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    # queryset = model.objects.all()
    ordering = "hostname"

    def get_queryset(self):
        if "srvmanager-show_disposed" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_disposed"] == "true":
                return self.model.objects.all().order_by(self.ordering)
        return self.model.objects.exclude(status__name="Disposed").order_by(
            self.ordering
        )


class DetailView(LoginRequiredMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(SuccessMessageMixin, LoginRequiredMixin, GenericUpdateView):
    success_message = "%(hostname)s " + _("was updated successfully")
    model = Model

    template_name = "%s/edit.html" % app_label

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, self.success_message % self.object.__dict__)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())

    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(SuccessMessageMixin, LoginRequiredMixin, GenericCreateView):
    success_message = "%(hostname)s " + _("was created successfully")
    model = Model

    template_name = "%s/edit.html" % app_label

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, self.success_message % self.object.__dict__)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())

    form_class = Form
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)


class DeleteView(LoginRequiredMixin, GenericDeleteView):
    success_message = "%(hostname)s " + _("was deleted successfully")
    template_name = "%s/delete.html" % app_label
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def form_valid(self, form):
        success_url = self.get_success_url()
        msg = self.success_message % {"hostname": getattr(self.object, "hostname")}
        self.object.delete()
        messages.success(self.request, msg)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(success_url)


class SearchView(LoginRequiredMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "hostname"
