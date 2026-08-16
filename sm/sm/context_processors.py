from django.conf import settings
from .views_onboarding import user_has_real_groups


def theme_settings(request):
    return {
        "THEME_CONTACT_EMAIL": getattr(
            settings, "THEME_CONTACT_EMAIL", "oliver@linux-kernel.at"
        ),
        "THEME_GITHUB_URL": getattr(
            settings, "THEME_GITHUB_URL", "https://github.com/ofalk/sm"
        ),
        "SOCIALACCOUNT_ENABLED": getattr(settings, "SOCIALACCOUNT_ENABLED", False),
        "APP_VERSION": getattr(settings, "APP_VERSION", "unknown"),
        "APP_MODIFICATION_DATE": getattr(settings, "APP_MODIFICATION_DATE", "unknown"),
        "ANALYTICS_ENABLED": getattr(settings, "ANALYTICS_ENABLED", False),
        "ANALYTICS_ID": getattr(settings, "ANALYTICS_ID", None),
        "ANALYTICS_BASE_URL": getattr(
            settings, "ANALYTICS_BASE_URL", "https://api.swetrix.com"
        ),
        "ONBOARDING_NEEDED": (
            getattr(request, "user", None) is not None
            and getattr(request.user, "is_authenticated", False)
            and not user_has_real_groups(request.user)
        ),
    }
