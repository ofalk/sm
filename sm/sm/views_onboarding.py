from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from typing import Any

from .models import Invitation
from uuid import UUID


def user_has_real_groups(user) -> bool:
    """
    A user is considered on-boarded once they are a member of at least one
    group that is not their automatically-created personal workspace.
    """
    for group in user.groups.all():
        if not group.name.endswith("'s Workspace"):
            return True
    return False


class GroupOnboardingView(LoginRequiredMixin, TemplateView):
    template_name = "group/onboarding.html"

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        context["onboarding_needed"] = not user_has_real_groups(self.request.user)
        return context

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        action = request.POST.get("action")
        if action == "join":
            token = request.POST.get("token", "").strip()
            try:
                UUID(token)
            except (ValueError, TypeError):
                messages.error(request, _("Invalid invitation token."))
                return self.get(request, *args, **kwargs)
            invitation = Invitation.objects.filter(token=token).first()
            if invitation is None:
                messages.error(request, _("Invalid invitation token."))
                return self.get(request, *args, **kwargs)
            return redirect("accept_invitation", token=token)
        if action == "create":
            return redirect("group_create")
        messages.warning(request, _("Please choose an action."))
        return self.get(request, *args, **kwargs)


class OnboardingBannerContext:
    """
    Small helper so templates can render an onboarding banner via the
    ``onboarding_needed`` context variable.
    """

    def __init__(self, request):
        self.request = request

    @property
    def needs_onboarding(self) -> bool:
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        return not user_has_real_groups(user)
