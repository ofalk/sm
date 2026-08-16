from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView
from typing import Any


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "account/profile.html"
    form_class = UserProfileForm

    def get_initial(self) -> dict:
        user = self.request.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form: Any) -> Any:
        form.save()
        messages.success(self.request, _("Your profile has been updated."))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return "/account/profile/"
