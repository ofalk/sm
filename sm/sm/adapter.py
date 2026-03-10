from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Connect existing local accounts with social accounts if emails match.
        """
        # sociallogin.is_existing: True if the user already has this specific social account connected
        if sociallogin.is_existing:
            return

        # If we have no email, we can't do anything
        if not sociallogin.email_address:
            return

        # Check if a user with this email already exists
        User = get_user_model()
        try:
            user = User.objects.get(email=sociallogin.email_address)
            # Link the social account to the existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
