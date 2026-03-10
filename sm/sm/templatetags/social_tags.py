from django import template

register = template.Library()

@register.simple_tag
def user_can_disconnect(user_social_auth):
    return user_social_auth.allowed_to_disconnect(
        user_social_auth.user,
        user_social_auth.provider)

@register.simple_tag(takes_context=True)
def get_social_providers_safe(context):
    """
    Safely returns social providers without crashing if request is missing.
    """
    request = context.get('request')
    if not request:
        return []
    
    try:
        from allauth.socialaccount.adapter import get_adapter
        adapter = get_adapter(request)
        return adapter.list_providers(request)
    except Exception:
        return []
