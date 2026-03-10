from django import template

register = template.Library()


@register.simple_tag
def user_can_disconnect(user_social_auth):
    return user_social_auth.allowed_to_disconnect(
        user_social_auth.user, user_social_auth.provider
    )


@register.simple_tag(takes_context=True)
def get_social_providers_safe(context):
    """
    Safely returns social providers without crashing if request is missing
    or if allauth.socialaccount is not in INSTALLED_APPS.
    """
    from django.conf import settings

    if not getattr(settings, "SOCIALACCOUNT_ENABLED", False):
        return []

    request = context.get("request") or getattr(context, "request", None)
    if not request:
        return []

    try:
        from allauth.socialaccount.adapter import get_adapter

        adapter = get_adapter(request)
        return adapter.list_providers(request)
    except Exception:
        return []


@register.filter
def provider_icon_class(provider_id):
    """
    Returns the correct FontAwesome class for a provider.
    """
    brands = [
        "facebook",
        "google",
        "github",
        "twitter",
        "linkedin",
        "apple",
        "microsoft",
        "slack",
    ]
    p_id = provider_id.lower()
    if p_id in brands:
        return f"fa-brands fa-{p_id}"
    return "fa-solid fa-share-alt"  # Fallback
