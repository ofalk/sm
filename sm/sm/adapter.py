from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Connect existing local accounts with social accounts if emails match.
        """
        if sociallogin.is_existing:
            return

        email_addresses = sociallogin.email_addresses
        if not email_addresses:
            return

        email = email_addresses[0].email

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
