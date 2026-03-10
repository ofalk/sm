import requests
from django.http import HttpResponse, HttpResponseRedirect
from django.core.cache import cache
from sm.utils import get_libravatar_url
from django.views.decorators.cache import cache_control


def avatar_proxy(request, email_hash):
    """
    Proxies libravatar images to allow for aggressive browser caching.
    """
    size = request.GET.get("s", 80)
    # Check cache first to avoid network hit
    cache_key = f"avatar_{email_hash}_{size}"
    cached_avatar = cache.get(cache_key)

    if cached_avatar:
        response = HttpResponse(
            cached_avatar["content"], content_type=cached_avatar["content_type"]
        )
        response["Cache-Control"] = "public, max-age=604800, immutable"
        return response

    # Fetch from libravatar (using hash directly if possible, or we just pass through)
    # For now, we'll just redirect to the real URL but with a script that fetches it
    # OR we fetch it here. Fetching is better for "hiding" the slow load.

    # Fetch from libravatar
    url = f"https://cdn.libravatar.org/avatar/{email_hash}?s={size}&d=mm"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "image/png")
            # Cache for 1 day in Django cache
            cache.set(
                cache_key, {"content": res.content, "content_type": content_type}, 86400
            )

            response = HttpResponse(res.content, content_type=content_type)
            response["Cache-Control"] = (
                "public, max-age=604800, immutable"  # 1 week browser cache
            )
            return response
    except Exception:
        pass

    return HttpResponseRedirect(url)
