from django import template
from django.urls import reverse
from sm.utils import get_email_hash

register = template.Library()

@register.simple_tag
def user_avatar_url(user, size=80):
    """
    Returns the URL for our caching avatar proxy.
    """
    email = getattr(user, 'email', '')
    email_hash = get_email_hash(email)
    return f"{reverse('avatar_proxy', args=[email_hash])}?s={size}"
