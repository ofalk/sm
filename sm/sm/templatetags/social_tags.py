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
    # Mapping of provider IDs to FontAwesome classes
    provider_map = {
        "facebook": "fa-brands fa-facebook",
        "google": "fa-brands fa-google",
        "github": "fa-brands fa-github",
        "gitlab": "fa-brands fa-gitlab",
        "twitter": "fa-brands fa-twitter",
        "linkedin": "fa-brands fa-linkedin",
        "apple": "fa-brands fa-apple",
        "microsoft": "fa-brands fa-microsoft",
        "slack": "fa-brands fa-slack",
        "oidc": "fa-solid fa-id-card-clip",
        "openid": "fa-solid fa-openid",
        "saml": "fa-solid fa-shield-halved",
        "okta": "fa-solid fa-id-card-clip",
        "keycloak": "fa-solid fa-key",
        "auth0": "fa-solid fa-shield-halved",
        "sso": "fa-solid fa-id-card-clip",
    }

    p_id = provider_id.lower()

    # Check for direct matches
    if p_id in provider_map:
        return provider_map[p_id]

    # Check for partial matches (e.g., 'google-oauth2' or 'google_custom')
    for key, value in provider_map.items():
        if key in p_id:
            return value

    return "fa-solid fa-share-nodes"  # Modern FA6 fallback icon
