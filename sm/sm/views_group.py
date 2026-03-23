from django.views.generic import ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Group
from .models import GroupProfile
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django import forms
from django.views import View
from typing import Any
from .utils_permissions import get_group_permissions_for_model


class GroupOwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        # Superusers can manage all groups
        if self.request.user.is_superuser:
            return True
        # Check if user is owner of at least one group
        return GroupProfile.objects.filter(owner=self.request.user).exists()


class GroupMemberListView(LoginRequiredMixin, GroupOwnerRequiredMixin, ListView):
    template_name = "group/member_list.html"
    context_object_name = "groups"

    def get_queryset(self) -> Any:
        if self.request.user.is_superuser:
            return Group.objects.all().prefetch_related("user_set", "profile")
        return Group.objects.filter(profile__owner=self.request.user).prefetch_related(
            "user_set", "profile"
        )


class AddGroupMemberForm(forms.Form):
    username = forms.CharField(label=_("Username or Email"))

    def clean_username(self) -> Any:
        username = self.cleaned_data["username"]
        try:
            if "@" in username:
                return User.objects.get(email=username)
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(_("User does not exist."))


class AddGroupMemberView(LoginRequiredMixin, GroupOwnerRequiredMixin, FormView):
    form_class = AddGroupMemberForm
    template_name = "group/add_member.html"

    def get_success_url(self) -> str:
        return reverse_lazy("group_member_list")

    def form_valid(self, form: Any) -> Any:
        group_id = self.kwargs.get("group_id")
        # Ensure the user is the owner OR a superuser
        if self.request.user.is_superuser:
            group = get_object_or_404(Group, pk=group_id)
        else:
            group = get_object_or_404(
                Group, pk=group_id, profile__owner=self.request.user
            )

        user_to_add = form.cleaned_data["username"]

        if group.user_set.count() >= group.profile.max_users:
            messages.error(
                self.request,
                _("User quota exceeded for this group (%d users).")
                % group.profile.max_users,
            )
            return self.form_invalid(form)

        group.user_set.add(user_to_add)
        messages.success(
            self.request,
            _("User %s added to group %s.") % (user_to_add.username, group.name),
        )
        return super().form_valid(form)


class RemoveGroupMemberView(LoginRequiredMixin, GroupOwnerRequiredMixin, View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        group_id = self.kwargs.get("group_id")
        user_id = self.kwargs.get("user_id")

        if self.request.user.is_superuser:
            group = get_object_or_404(Group, pk=group_id)
        else:
            group = get_object_or_404(
                Group, pk=group_id, profile__owner=self.request.user
            )

        user_to_remove = get_object_or_404(User, pk=user_id)

        if user_to_remove == self.request.user and not self.request.user.is_superuser:
            messages.error(
                request, _("You cannot remove yourself from your own group.")
            )
        else:
            group.user_set.remove(user_to_remove)
            messages.success(
                request,
                _("User %s removed from group %s.")
                % (user_to_remove.username, group.name),
            )

        return redirect("group_member_list")


class GroupPermissionForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.group = kwargs.pop("group")
        super().__init__(*args, **kwargs)

        self.models_to_manage = [
            ("server", _("Servers")),
            ("cluster", _("Clusters")),
            ("domain", _("Domains")),
            ("vendor", _("Vendors")),
            ("operatingsystem", _("Operating Systems")),
        ]

        current_perms = self.group.permissions.all().values_list("codename", flat=True)

        for app_label, label in self.models_to_manage:
            # Find the actual change permission codename which might be 'change_model'
            # because we named our model 'Model'
            perms = get_group_permissions_for_model(app_label)
            change_perm = next(
                (p for p in perms if p.codename.startswith("change_")), None
            )

            initial_val = False
            if change_perm:
                initial_val = change_perm.codename in current_perms

            self.fields[f"edit_{app_label}"] = forms.BooleanField(
                label=_("Can Edit %s") % label,
                required=False,
                initial=initial_val,
            )

    def save(self) -> None:
        for app_label_tuple in self.models_to_manage:
            app_label = app_label_tuple[0]
            perms = get_group_permissions_for_model(app_label)
            # We manage add, change, delete as "Edit"
            edit_perms = [
                p
                for p in perms
                if p.codename.startswith(("add_", "change_", "delete_"))
            ]

            if self.cleaned_data.get(f"edit_{app_label}"):
                self.group.permissions.add(*edit_perms)
            else:
                self.group.permissions.remove(*edit_perms)


class GroupPermissionUpdateView(LoginRequiredMixin, GroupOwnerRequiredMixin, FormView):
    template_name = "group/permission_edit.html"
    form_class = GroupPermissionForm

    def get_form_kwargs(self) -> Any:
        kwargs = super().get_form_kwargs()
        group_id = self.kwargs.get("group_id")
        if self.request.user.is_superuser:
            kwargs["group"] = get_object_or_404(Group, pk=group_id)
        else:
            kwargs["group"] = get_object_or_404(
                Group, pk=group_id, profile__owner=self.request.user
            )
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy("group_member_list")

    def form_valid(self, form: Any) -> Any:
        form.save()
        messages.success(self.request, _("Group permissions updated successfully."))
        return super().form_valid(form)
