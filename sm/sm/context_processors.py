from django.conf import settings


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
    }
