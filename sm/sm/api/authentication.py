from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from sm.models import ApiKey

MALFORMED_MESSAGE = (
    "Invalid Authorization header. Expected format: " "ApiKey <client_id>:<secret>"
)


class ApiKeyAuthentication(BaseAuthentication):
    """
    Authenticates requests using a client_id/secret API key pair.

    The credentials are supplied in the Authorization header:

        Authorization: ApiKey <client_id>:<secret>

    A successful authentication returns the user the key belongs to, so all
    further permission and multi-tenancy checks behave exactly as they would
    for that user.
    """

    keyword = "ApiKey"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) != 2:
            raise AuthenticationFailed(MALFORMED_MESSAGE)

        token = auth[1].decode("utf-8")
        if ":" not in token:
            raise AuthenticationFailed(MALFORMED_MESSAGE)

        client_id, secret = token.split(":", 1)

        key = (
            ApiKey.objects.select_related("user")
            .filter(client_id=client_id, is_active=True)
            .first()
        )
        if key is None or not check_password(secret, key.secret_hash):
            raise AuthenticationFailed("Invalid API key credentials.")

        if not key.user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        # Only write on a change to avoid a DB update on every single request.
        if not key.last_used_at or timezone.now() - key.last_used_at > timedelta(
            minutes=5
        ):
            ApiKey.objects.filter(pk=key.pk).update(last_used_at=timezone.now())

        return (key.user, key)

    def authenticate_header(self, request):
        return self.keyword


class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = ApiKeyAuthentication
    name = "ApiKeyAuth"

    def get_security_requirement(self, auto_schema):
        return {self.name: []}

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": (
                "Client ID/secret pair. Send the credentials as "
                "`ApiKey <client_id>:<secret>` in the Authorization header."
            ),
        }
