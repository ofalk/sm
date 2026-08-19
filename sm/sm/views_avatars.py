import logging
import re

import requests
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.cache import cache

logger = logging.getLogger(__name__)

# libravatar only serves md5 email hashes (32 lowercase hex chars).
_HASH_RE = re.compile(r"^[0-9a-f]{32}$")
_MAX_SIZE = 512


def _validate_size(raw):
    try:
        size = int(raw)
    except (TypeError, ValueError):
        size = 80
    return min(max(size, 1), _MAX_SIZE)


def avatar_proxy(request, email_hash):
    """
    Proxies libravatar images to allow for aggressive browser caching.

    The ``email_hash`` must be a valid 32-char md5 hex digest and ``s`` is
    validated to a bounded integer so the endpoint can't be used to probe
    arbitrary libravatar URLs.
    """
    if not _HASH_RE.match(email_hash.lower()):
        return HttpResponseBadRequest("invalid email hash")

    size = _validate_size(request.GET.get("s", 80))
    cache_key = f"avatar_{email_hash}_{size}"
    cached_avatar = cache.get(cache_key)

    if cached_avatar:
        response = HttpResponse(
            cached_avatar["content"], content_type=cached_avatar["content_type"]
        )
        response["Cache-Control"] = "public, max-age=604800, immutable"
        return response

    url = f"https://cdn.libravatar.org/avatar/{email_hash}?s={size}&d=mm"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "image/png")
            cache.set(
                cache_key, {"content": res.content, "content_type": content_type}, 86400
            )

            response = HttpResponse(res.content, content_type=content_type)
            response["Cache-Control"] = "public, max-age=604800, immutable"
            return response
    except Exception:
        logger.exception("Avatar proxy: failed to fetch %s", email_hash)

    return HttpResponseRedirect(url)
