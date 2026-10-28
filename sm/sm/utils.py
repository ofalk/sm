import hashlib
import json
import random
import string

from django.utils.safestring import mark_safe


def json_for_script(value):
    """
    Serialize ``value`` for embedding in an inline ``<script>`` block.

    Escapes the characters that could terminate the surrounding ``<script>``
    element (``<``, ``>`` and ``&``), so a value such as
    ``</script><script>alert(1)</script>`` cannot break out of the block.
    """
    return mark_safe(
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def get_email_hash(email):
    """
    Returns MD5 hash of lowercase email for avatar services.
    """
    if not email:
        return "00000000000000000000000000000000"
    return hashlib.md5(email.lower().encode("utf-8")).hexdigest()


def random_string(len=10):
    return "".join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(10)
    )


def random_number(start=0, end=10):
    return random.randint(start, end)
