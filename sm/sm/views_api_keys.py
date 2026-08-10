from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
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
        key, secret = ApiKey.create_for_user(self.request.user, name)

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
        key.save(update_fields=["is_active"])
        messages.success(
            request,
            _("API key %(key)s has been revoked.") % {"key": key},
        )
        return redirect("api_keys")
