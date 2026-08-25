import os
import dj_database_url
from pathlib import Path
from sys import platform, argv
import django.contrib.messages as messages
from django.core.exceptions import ImproperlyConfigured
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment-based configuration
DEBUG = config("DEBUG", default=False, cast=bool)

TEST_RUNNER = "sm.runner.SmTestRunner"
_cfg_secret = config("SECRET_KEY", default="")
if not _cfg_secret:
    if DEBUG:
        _cfg_secret = "django-insecure-default-key-for-dev"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")
SECRET_KEY = _cfg_secret
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

THEME_CONTACT_EMAIL = config("THEME_CONTACT_EMAIL", default="oliver@linux-kernel.at")
THEME_GITHUB_URL = config("THEME_GITHUB_URL", default="https://github.com/ofalk/sm")

# Send an email to group members + superusers when a server's status changes.
SERVER_STATUS_NOTIFY = config("SERVER_STATUS_NOTIFY", default=False, cast=bool)

# Version information
APP_VERSION = config("APP_VERSION", default="unknown")
APP_MODIFICATION_DATE = config("APP_MODIFICATION_DATE", default="unknown")

if APP_VERSION == "unknown" or APP_MODIFICATION_DATE == "unknown":
    try:
        import subprocess

        if APP_VERSION == "unknown":
            APP_VERSION = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
                )
                .decode("utf-8")
                .strip()
            )
        if APP_MODIFICATION_DATE == "unknown":
            APP_MODIFICATION_DATE = (
                subprocess.check_output(
                    ["git", "log", "-1", "--format=%cd"], stderr=subprocess.DEVNULL
                )
                .decode("utf-8")
                .strip()
            )
    except Exception:
        pass

DISABLE_SOCIAL_AUTH = config("DISABLE_SOCIAL_AUTH", default=False, cast=bool)

# Analytics settings
ANALYTICS_ENABLED = config("ANALYTICS_ENABLED", default=False, cast=bool)
ANALYTICS_ID = config("ANALYTICS_ID", default=None)
ANALYTICS_BASE_URL = config("ANALYTICS_BASE_URL", default="https://api.swetrix.com")

# Application definition

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.admindocs",
    "rest_framework",
    "django_bootstrap5",
    "django_countries",
    "taggit",
    "simple_history",
    "drf_spectacular",
    # Allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.mfa",
    "social_django",
]

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]

if not DISABLE_SOCIAL_AUTH:
    INSTALLED_APPS += [
        "allauth.socialaccount.providers.google",
        "allauth.socialaccount.providers.openid_connect",
    ]
    SOCIALACCOUNT_ENABLED = True
else:
    SOCIALACCOUNT_ENABLED = False

INSTALLED_APPS += [
    # Project Apps
    "cluster",
    "operatingsystem",
    "clusterpackage",
    "patchtime",
    "location",
    "servermodel",
    "server",
    "status",
    "domain",
    "clustersoftware",
    "clusterpackagetype",
    "vendor",
    "sm.apps.SmConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "htmlmin.middleware.HtmlMinifyMiddleware",
    "htmlmin.middleware.MarkRequestMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    # Allauth middleware
    "allauth.account.middleware.AccountMiddleware",
]

if DEBUG:
    # Insert DebugToolbarMiddleware after SessionMiddleware but before CommonMiddleware
    try:
        session_idx = MIDDLEWARE.index(
            "django.contrib.sessions.middleware.SessionMiddleware"
        )
        MIDDLEWARE.insert(
            session_idx + 1, "debug_toolbar.middleware.DebugToolbarMiddleware"
        )
    except ValueError:
        MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "sm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "sm" / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "sm.context_processors.theme_settings",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "sm.template.loaders.app_directories_enhanced.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "sm.wsgi.application"

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
elif "test" in argv:
    # LiveServerTestCase passes the shared in-memory connection to the live
    # server thread, which is the configuration Django explicitly recommends
    # for threaded live-server tests (see LiveServerTestCase source). WAL +
    # busy timeout (set in sm/signals.py) further harden against locks.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "OPTIONS": {"timeout": 30},
        }
    }
elif platform == "darwin":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Use config_local or environment variables for MySQL if needed
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

if "test" in argv:
    # Persistent connections (CONN_MAX_AGE) make each live-server request
    # thread keep an idle PostgreSQL session open, which then prevents
    # dropping the test database ("database is being accessed by other
    # users"). Force connection-per-request while testing.
    for db_config in DATABASES.values():
        db_config["CONN_MAX_AGE"] = 0

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Path where application-level translations live (po/mo files).
LOCALE_PATHS = [
    BASE_DIR / "sm" / "locale",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [
    BASE_DIR / "sm" / "static",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Extra settings

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth settings
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/"
ACCOUNT_LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Social Auth (Legacy/Transition)
SOCIAL_AUTH_STRATEGY = "social_django.strategy.DjangoStrategy"
SOCIAL_AUTH_STORAGE = "social_django.models.DjangoStorage"

# Disable MFA features that might cause issues if allauth.mfa is not fully configured
MFA_PASSKEY_LOGIN_ENABLED = False
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]

if not DISABLE_SOCIAL_AUTH:
    SOCIALACCOUNT_AUTO_SIGNUP = True
    SOCIALACCOUNT_ADAPTER = "sm.adapter.MySocialAccountAdapter"

    SOCIALACCOUNT_PROVIDERS = {}

    # Google Auth
    google_id = config("GOOGLE_CLIENT_ID", default=None)
    google_secret = config("GOOGLE_SECRET", default=None)
    if google_id and google_secret:
        SOCIALACCOUNT_PROVIDERS["google"] = {
            "APPS": [
                {
                    "client_id": google_id,
                    "secret": google_secret,
                    "settings": {
                        "scope": ["profile", "email"],
                        "auth_params": {"access_type": "online"},
                    },
                }
            ]
        }

    # Generic OIDC
    oidc_id = config("OIDC_CLIENT_ID", default=None)
    oidc_secret = config("OIDC_SECRET", default=None)
    oidc_url = config("OIDC_URL", default=None)
    oidc_name = config("OIDC_NAME", default="Localghost SSO")

    if oidc_id and oidc_secret and oidc_url:
        SOCIALACCOUNT_PROVIDERS["openid_connect"] = {
            "APPS": [
                {
                    "provider_id": "oidc",
                    "name": oidc_name,
                    "client_id": oidc_id,
                    "secret": oidc_secret,
                    "settings": {"server_url": oidc_url},
                }
            ]
        }

INTERNAL_IPS = [
    "127.0.0.1",
]

MESSAGE_TAGS = {messages.ERROR: "danger"}

MESSAGE_STORAGE = "django.contrib.messages.storage.fallback.FallbackStorage"

TAGGIT_CASE_INSENSITIVE = True

# REST Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "sm.api.authentication.ApiKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/hour",
        "anon": "100/hour",
    },
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ServerManager API",
    "DESCRIPTION": "API for managing servers, clusters, and infrastructure.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Bootstrap 5 settings
BOOTSTRAP5 = {
    "error_css_class": "bootstrap5-error",
    "required_css_class": "bootstrap5-required",
    "javascript_in_head": True,
    "success_css_class": "bootstrap5-bound",
}

HTML_MINIFY = True

# Security hardening (only applied when not in DEBUG so local HTTP dev works).
# Skipped while running the test suite, which always runs with DEBUG=False and
# uses plain-HTTP requests that SECURE_SSL_REDIRECT would redirect away.
if not DEBUG and "test" not in argv:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
    CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

if not DISABLE_SOCIAL_AUTH and os.path.isfile(BASE_DIR / "config_local.py"):
    from config_local import *  # noqa

# Redefine to ensure no social_core backends survive in quick test mode
if DISABLE_SOCIAL_AUTH:
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]
