from django.views.generic import ListView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .models import GroupProfile, Invitation
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django import forms
from django.views import View
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from typing import Any
from .utils_permissions import (
    get_group_permissions_for_model,
    APP_MODELS,
    MODEL_LABELS,
)
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse


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
        return (
            Group.objects.filter(
                Q(profile__owner=self.request.user) | Q(user=self.request.user)
            )
            .prefetch_related("user_set", "profile")
            .distinct()
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


class CreateGroupForm(forms.Form):
    name = forms.CharField(label=_("Group Name"), max_length=150)
    max_users = forms.IntegerField(
        label=_("Max Users"),
        initial=10,
        min_value=2,
        max_value=100,
        help_text=_("Maximum number of users in this group"),
    )


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
            (app_label, MODEL_LABELS.get(app_label, app_label))
            for app_label, _model in APP_MODELS
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


class UserPermissionForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop("user")
        self.group = kwargs.pop("group")
        super().__init__(*args, **kwargs)

        self.models_to_manage = [
            (app_label, MODEL_LABELS.get(app_label, app_label))
            for app_label, _model in APP_MODELS
        ]

        group_perms = self.group.permissions.all().values_list("codename", flat=True)
        user_perms = self.user.user_permissions.all().values_list("codename", flat=True)

        for app_label, label in self.models_to_manage:
            perms = get_group_permissions_for_model(app_label)
            change_perm = next(
                (p for p in perms if p.codename.startswith("change_")), None
            )

            initial_val = False
            if change_perm:
                initial_val = change_perm.codename in user_perms

            inherited = change_perm.codename in group_perms if change_perm else False

            self.fields[f"edit_{app_label}"] = forms.BooleanField(
                label=_("Can Edit %s") % label,
                required=False,
                initial=initial_val,
            )
            if inherited:
                self.fields[f"edit_{app_label}"].help_text = _("(Inherited from group)")

    def save(self) -> None:
        for app_label_tuple in self.models_to_manage:
            app_label = app_label_tuple[0]
            perms = get_group_permissions_for_model(app_label)
            edit_perms = [
                p
                for p in perms
                if p.codename.startswith(("add_", "change_", "delete_"))
            ]

            if self.cleaned_data.get(f"edit_{app_label}"):
                self.user.user_permissions.add(*edit_perms)
            else:
                self.user.user_permissions.remove(*edit_perms)


class UserPermissionUpdateView(LoginRequiredMixin, GroupOwnerRequiredMixin, FormView):
    template_name = "group/user_permission_edit.html"
    form_class = UserPermissionForm

    def get_form_kwargs(self) -> Any:
        kwargs = super().get_form_kwargs()
        group_id = self.kwargs.get("group_id")
        user_id = self.kwargs.get("user_id")
        if self.request.user.is_superuser:
            group = get_object_or_404(Group, pk=group_id)
        else:
            group = get_object_or_404(
                Group, pk=group_id, profile__owner=self.request.user
            )
        # Only group owners may edit the permissions of their own group's
        # members. Without the membership check an owner could grant/revoke
        # the (global) user permissions of arbitrary users in other groups.
        kwargs["group"] = group
        kwargs["user"] = get_object_or_404(User, pk=user_id, groups=group)
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy("group_member_list")

    def form_valid(self, form: Any) -> Any:
        form.save()
        messages.success(self.request, _("User permissions updated successfully."))
        return super().form_valid(form)


class InviteGroupMemberForm(forms.Form):
    email = forms.EmailField(label=_("Email Address"))

    def clean_email(self) -> Any:
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email.lower()


class InviteGroupMemberView(LoginRequiredMixin, GroupOwnerRequiredMixin, FormView):
    form_class = InviteGroupMemberForm
    template_name = "group/invite_member.html"

    def get_success_url(self) -> str:
        return reverse_lazy("group_member_list")

    def get_group(self) -> Group:
        group_id = self.kwargs.get("group_id")
        if self.request.user.is_superuser:
            return get_object_or_404(Group, pk=group_id)
        return get_object_or_404(Group, pk=group_id, profile__owner=self.request.user)

    def form_valid(self, form: Any) -> Any:
        group = self.get_group()
        email = form.cleaned_data["email"]

        existing_invitation = Invitation.objects.filter(
            email__iexact=email, group=group
        ).first()
        if existing_invitation and not existing_invitation.is_expired():
            messages.error(
                self.request,
                _("An invitation has already been sent to this email address."),
            )
            return self.form_invalid(form)

        # Replace any expired/used invitation for the same email+group so we
        # don't trip the (email, group) unique constraint.
        Invitation.objects.filter(email__iexact=email, group=group).delete()

        invitation = Invitation.objects.create(
            email=email,
            group=group,
            created_by=self.request.user,
        )

        self.send_invitation_email(invitation)

        messages.success(
            self.request,
            _("Invitation sent to %(email)s.") % {"email": email},
        )
        return super().form_valid(form)

    def send_invitation_email(self, invitation: Invitation) -> None:
        invite_url = self.request.build_absolute_uri(
            reverse("accept_invitation", kwargs={"token": invitation.token})
        )
        subject = _("Invitation to join %(group_name)s on ServerManager") % {
            "group_name": invitation.group.name
        }
        message = render_to_string(
            "group/email/invite.txt",
            {
                "invitation": invitation,
                "invite_url": invite_url,
                "owner_name": (
                    invitation.created_by.username
                    if invitation.created_by
                    else "An administrator"
                ),
            },
        )
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@servermanager"),
            [invitation.email],
            fail_silently=False,
        )


class AcceptInvitationView(TemplateView):
    template_name = "group/accept_invitation.html"

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        token = self.kwargs.get("token")
        invitation = get_object_or_404(Invitation, token=token)

        if invitation.is_expired():
            context["error"] = _("This invitation has expired.")
            return context

        if invitation.accepted_at:
            context["error"] = _("This invitation has already been used.")
            return context

        context["invitation"] = invitation
        return context

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        token = self.kwargs.get("token")
        invitation = get_object_or_404(Invitation, token=token)

        if invitation.is_expired() or invitation.accepted_at:
            messages.error(request, _("This invitation is no longer valid."))
            return redirect("account_login")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        if not username or not email or not password:
            messages.error(request, _("All fields are required."))
            return self.get(request, *args, **kwargs)

        if password != password_confirm:
            messages.error(request, _("Passwords do not match."))
            return self.get(request, *args, **kwargs)

        # The invitee must claim the invited account under the invited email,
        # otherwise anyone with the link could register a new identity.
        if email.lower() != invitation.email.lower():
            messages.error(request, _("The email does not match the invitation."))
            return self.get(request, *args, **kwargs)

        try:
            validate_password(password)
        except ValidationError as exc:
            messages.error(
                request, _("Password is not strong enough: %s") % " ".join(exc.messages)
            )
            return self.get(request, *args, **kwargs)

        if User.objects.filter(username=username).exists():
            messages.error(request, _("Username already exists."))
            return self.get(request, *args, **kwargs)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, _("Email already registered."))
            return self.get(request, *args, **kwargs)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        invitation.group.user_set.add(user)
        invitation.accepted_at = timezone.now()
        invitation.save()

        messages.success(
            request,
            _("You have joined %(group_name)s!")
            % {"group_name": invitation.group.name},
        )

        from django.contrib.auth import login

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        return redirect("dashboard")


class GroupFilterView(View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        # Support both the checkbox format ("1,2,3" in `groups`) and the
        # single-select format (a `group` field) used by the search filter.
        groups_param = request.POST.get("groups", "")
        single = request.POST.get("group", "")
        if groups_param:
            # Only allow selecting groups the user actually belongs to, so a
            # user can never filter into another tenant's data.
            user_group_ids = set(request.user.groups.values_list("id", flat=True))
            selected_groups = [
                g
                for g in groups_param.split(",")
                if g.isdigit() and int(g) in user_group_ids
            ]
        elif single:
            user_group_ids = set(request.user.groups.values_list("id", flat=True))
            selected_groups = [
                single
            ] if (single.isdigit() and int(single) in user_group_ids) else []
        else:
            selected_groups = []

        if selected_groups:
            request.session["selected_groups"] = selected_groups
        else:
            request.session["selected_groups"] = []

        request.session.modified = True

        # If a `next` URL was provided, redirect there so the filter applies
        # to the referring page (e.g. search results).
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            from django.shortcuts import redirect

            return redirect(next_url)

        return JsonResponse({"status": "success"})


class GroupCreateView(LoginRequiredMixin, FormView):
    form_class = CreateGroupForm
    template_name = "group/member_list.html"
    success_url = reverse_lazy("group_member_list")

    def form_valid(self, form: Any) -> Any:
        name = form.cleaned_data["name"]
        max_users = form.cleaned_data.get("max_users", 10)

        max_groups = 5
        owned_groups_count = self.request.user.owned_groups.count()
        if owned_groups_count >= max_groups:
            messages.error(
                self.request,
                _("You can only create up to %d groups.") % max_groups,
            )
            return redirect("group_member_list")

        existing = Group.objects.filter(name=name).first()
        if existing:
            messages.error(self.request, _("A group with this name already exists."))
            return redirect("group_member_list")

        group = Group.objects.create(name=name)
        # Profile is already created by create_group_profile signal
        profile = group.profile
        profile.owner = self.request.user
        profile.max_users = max_users
        profile.save()

        self.request.user.groups.add(group)

        from .utils_permissions import sync_group_permissions

        sync_group_permissions(group, grant_all=True)

        messages.success(self.request, _("Group '%s' created successfully.") % name)
        return super().form_valid(form)

    def form_invalid(self, form: Any) -> Any:
        messages.error(self.request, _("Failed to create group."))
        return redirect("group_member_list")
