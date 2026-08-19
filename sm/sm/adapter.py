from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Connect an existing local account to a social account only when the
        provider has verified a matching email address.
        """
        if sociallogin.is_existing:
            return

        User = get_user_model()
        for email_address in sociallogin.email_addresses:
            if not email_address.verified:
                continue
            try:
                user = User.objects.get(email=email_address.email)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                continue
            sociallogin.connect(request, user)
            return
