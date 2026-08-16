from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView
from typing import Any

from .models import ApiKey


class CreateApiKeyForm(forms.Form):
    name = forms.CharField(
        label=_("Name (optional)"),
        max_length=100,
        required=False,
        help_text=_("A label to remember this key by."),
    )
    expires_in_days = forms.IntegerField(
        label=_("Expire after (days)"),
        required=False,
        min_value=1,
        max_value=3650,
        initial=90,
        help_text=_("Optional. The key will be rejected after this many days."),
    )

    def clean_expires_in_days(self) -> int:
        value = self.cleaned_data.get("expires_in_days")
        return value or 0


class ApiKeyListView(LoginRequiredMixin, FormView):
    template_name = "api_keys/list.html"
    form_class = CreateApiKeyForm
    success_url = reverse_lazy("api_keys")

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        context["api_keys"] = self.request.user.api_keys.all()
        return context

    def form_valid(self, form: Any) -> Any:
        name = form.cleaned_data["name"].strip()
        expires_in_days = form.cleaned_data.get("expires_in_days") or 0
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timedelta(days=expires_in_days)
        key, secret = ApiKey.create_for_user(
            self.request.user, name, expires_at=expires_at
        )

        context = self.get_context_data(form=form)
        context["new_key"] = key
        context["new_secret"] = secret
        messages.success(
            self.request,
            _("API key created. Copy the secret now - it will not be shown again."),
        )
        return self.render_to_response(context)


class RevokeApiKeyView(LoginRequiredMixin, View):
    def post(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Any:
        key = get_object_or_404(ApiKey, pk=pk, user=request.user)
        key.is_active = False
        key.revoked_at = timezone.now()
        key.save(update_fields=["is_active", "revoked_at"])
        messages.success(
            request,
            _("API key %(key)s has been revoked.") % {"key": key},
        )
        return redirect("api_keys")


class RotateApiKeyView(LoginRequiredMixin, FormView):
    form_class = CreateApiKeyForm
    template_name = "api_keys/list.html"
    success_url = reverse_lazy("api_keys")

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        pk = kwargs.get("pk")
        key = get_object_or_404(ApiKey, pk=pk, user=request.user)
        new_key, new_secret = key.rotate(name=key.name)

        context = self.get_context_data()
        context["api_keys"] = request.user.api_keys.all()
        context["new_key"] = new_key
        context["new_secret"] = new_secret
        messages.success(
            request,
            _("API key %(key)s has been rotated. Copy the new secret now.")
            % {"key": key},
        )
        return self.render_to_response(context)
