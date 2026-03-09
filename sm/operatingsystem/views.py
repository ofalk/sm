from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Model
from .forms import Form, FormDisabled
from . import app_label

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

from django.urls import reverse_lazy

from django.contrib import messages


class ListView(LoginRequiredMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "vendor"

    def get_queryset(self):
        from vendor.models import Model as VendorModel

        if "srvmanager-show_empty" in self.request.COOKIES:
            if self.request.COOKIES["srvmanager-show_empty"] == "false":
                return VendorModel.objects.exclude(operatingsystem=None).order_by(
                    "name"
                )
        return VendorModel.objects.all().order_by("name")


class DetailView(LoginRequiredMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled


class UpdateView(SuccessMessageMixin, LoginRequiredMixin, GenericUpdateView):
    success_message = "%(version)s " + _("was updated successfully")
    template_name = "%s/edit.html" % app_label
    model = Model
    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, self.success_message % self.object.__dict__)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())


class CreateView(SuccessMessageMixin, LoginRequiredMixin, GenericCreateView):
    success_message = "%(version)s " + _("was created successfully")

    template_name = "%s/edit.html" % app_label
    fields = "__all__"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def get_initial(self):
        from vendor.models import Model as VendorModel

        initial = super().get_initial()
        if "vendor" in self.kwargs:
            initial["vendor"] = VendorModel.objects.filter(
                pk=self.kwargs["vendor"]
            ).first()
        return initial

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, self.success_message % self.object.__dict__)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())


class DeleteView(LoginRequiredMixin, GenericDeleteView):
    success_message = "%(version)s " + _("was deleted successfully")
    template_name = "%s/delete.html" % app_label
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def form_valid(self, form):
        success_url = self.get_success_url()
        msg = self.success_message % {"version": getattr(self.object, "version")}
        self.object.delete()
        messages.success(self.request, msg)
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(success_url)
