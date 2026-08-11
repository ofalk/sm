from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from sm.views import SafeDeleteMixin


from .models import Model
from .forms import Form, FormDisabled
from . import app_label

from django.views.generic import ListView as GenericListView
from django.views.generic.edit import UpdateView as GenericUpdateView
from django.views.generic.edit import CreateView as GenericCreateView
from django.views.generic.edit import DeleteView as GenericDeleteView
from django.contrib.messages.views import SuccessMessageMixin

from django.utils.translation import gettext as _

try:
    from django.urls import reverse_lazy
except Exception:  # pragma: no cover
    from django.urls import reverse_lazy  # pragma: no cover


def _get_group_for_user(user):
    if user.is_superuser:
        return None
    groups = user.groups.all()
    return groups.first() if groups.exists() else None


class ListView(LoginRequiredMixin, GenericListView):
    template_name = "%s/list.html" % app_label
    model = Model
    paginate_by = 20
    paginate_orphans = paginate_by / 4
    ordering = "name"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset.order_by(self.ordering)
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups).order_by(self.ordering)


class DetailView(LoginRequiredMixin, GenericUpdateView):
    template_name = "%s/detail.html" % app_label
    model = Model
    form_class = FormDisabled

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups)


class UpdateView(SuccessMessageMixin, LoginRequiredMixin, GenericUpdateView):
    success_message = "%(name)s " + _("was updated successfully")

    template_name = "%s/edit.html" % app_label
    model = Model

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.group = _get_group_for_user(self.request.user)
        self.object.save()
        messages.success(self.request, self.success_message % self.object.__dict__)

        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups)

    form_class = Form
    success_url = reverse_lazy("%s:index" % app_label)


class CreateView(SuccessMessageMixin, LoginRequiredMixin, GenericCreateView):
    success_message = "%(name)s " + _("was created successfully")

    template_name = "%s/edit.html" % app_label
    form_class = Form
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.group = _get_group_for_user(self.request.user)
        self.object.save()
        messages.success(self.request, self.success_message % self.object.__dict__)

        return HttpResponseRedirect(self.get_success_url())


class DeleteView(SafeDeleteMixin, LoginRequiredMixin, GenericDeleteView):
    success_message = "%(name)s " + _("was deleted successfully")
    template_name = "delete.html"
    model = Model
    success_url = reverse_lazy("%s:index" % app_label)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        user_groups = self.request.user.groups.all()
        return queryset.filter(cluster__group__in=user_groups)
