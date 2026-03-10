from django import template
from sm.utils import get_libravatar_url

register = template.Library()

@register.simple_tag
def user_avatar_url(user, size=80):
    """
    Returns the Libravatar URL for the given user.
    """
    email = getattr(user, 'email', '')
    return get_libravatar_url(email, size=size)
