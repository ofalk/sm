from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User, Group
from .models import GroupProfile
from .forms_admin import GroupProfileForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from typing import Any


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_staff


class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = "admin/user_list.html"
    context_object_name = "users"
    ordering = "username"

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        context["groups"] = Group.objects.all().prefetch_related("profile")
        return context


class GroupProfileUpdateView(StaffRequiredMixin, UpdateView):
    model = GroupProfile
    form_class = GroupProfileForm
    template_name = "admin/group_profile_edit.html"
    success_url = reverse_lazy("user_management_list")

    def form_valid(self, form: Any) -> Any:
        response = super().form_valid(form)
        messages.success(self.request, _("Group profile updated successfully."))
        return response
