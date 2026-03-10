import os
import dj_database_url
from pathlib import Path
from sys import platform, argv
import django.contrib.messages as messages
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment-based configuration
SECRET_KEY = config("SECRET_KEY", default="django-insecure-default-key-for-dev")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

THEME_CONTACT_EMAIL = config("THEME_CONTACT_EMAIL", default="oliver@linux-kernel.at")
THEME_GITHUB_URL = config("THEME_GITHUB_URL", default="https://github.com/ofalk/sm")

DISABLE_SOCIAL_AUTH = config("DISABLE_SOCIAL_AUTH", default=False, cast=bool)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.admindocs",
    "rest_framework",
    "bootstrap4",
    "debug_toolbar",
    "django_countries",
    "whitenoise.runserver_nostatic",
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

if not DISABLE_SOCIAL_AUTH:
    INSTALLED_APPS += [
        #        "allauth.socialaccount.providers.facebook",
        "allauth.socialaccount.providers.google",
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
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "htmlmin.middleware.HtmlMinifyMiddleware",
    "htmlmin.middleware.MarkRequestMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    # Allauth middleware
    "allauth.account.middleware.AccountMiddleware",
]

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
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

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

    SOCIALACCOUNT_PROVIDERS = {
        #        "facebook": {
        #            "METHOD": "oauth2",
        #            "SCOPE": ["email", "public_profile"],
        #            "AUTH_PARAMS": {"auth_type": "reauthenticate"},
        #            "INIT_PARAMS": {"cookie": True},
        #            "FIELDS": [
        #                "id",
        #                "first_name",
        #                "last_name",
        #                "middle_name",
        #                "name",
        #                "name_format",
        #                "picture",
        #                "short_name",
        #            ],
        #            "EXCHANGE_TOKEN": True,
        #            "VERIFIED_EMAIL": False,
        #            "VERSION": "v13.0",
        #        },
        "google": {
            "SCOPE": [
                "profile",
                "email",
            ],
            "AUTH_PARAMS": {
                "access_type": "online",
            },
            "AUTH_PKCE_ENABLED": True,
            "FETCH_USERINFO": True,
        }
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
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ServerManager API",
    "DESCRIPTION": "API for managing servers, clusters, and infrastructure.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Bootstrap 4 settings
BOOTSTRAP4 = {
    "error_css_class": "bootstrap4-error",
    "required_css_class": "bootstrap4-required",
    "javascript_in_head": True,
    "success_css_class": "bootstrap4-bound",
}

HTML_MINIFY = True

if not DISABLE_SOCIAL_AUTH and os.path.isfile(BASE_DIR / "config_local.py"):
    from config_local import *  # noqa

# Redefine to ensure no social_core backends survive in quick test mode
if DISABLE_SOCIAL_AUTH:
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]
