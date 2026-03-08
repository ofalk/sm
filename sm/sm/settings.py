import os
from pathlib import Path
from sys import platform, argv
import django.contrib.messages as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

SECRET_KEY = os.environ.get('SECRET_KEY', 'c#s9btkc36=@8q^n#!c+%z+ne6*uzy)bc3f+*97^s-c8*f)^+8')

DEBUG = True

ALLOWED_HOSTS = [
    'sm.linux-kernel.at',
    'sm.dev.linux-kernel.at',
    'zipfer.linux-kernel.at',
    'localhost',
    '127.0.0.1',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.admindocs',

    'rest_framework',
    'django_extensions',
    'bootstrap4',
    'debug_toolbar',
    'django_countries',
    'whitenoise.runserver_nostatic',
    'taggit',
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.mfa',

    # Project Apps
    'cluster',
    'operatingsystem',
    'clusterpackage',
    'patchtime',
    'location',
    'servermodel',
    'server',
    'status',
    'domain',
    'clustersoftware',
    'clusterpackagetype',
    'vendor',
    'sm',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    # Allauth middleware
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'sm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'sm' / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'sm.template.loaders.app_directories_enhanced.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'sm.wsgi.application'

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

if 'test' in argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif platform == 'darwin':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Use config_local or environment variables for MySQL if needed
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Extra settings

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name'
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v13.0',
    }
}

INTERNAL_IPS = [
    '127.0.0.1',
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

TAGGIT_CASE_INSENSITIVE = True

# Bootstrap 4 settings
BOOTSTRAP4 = {
    'error_css_class': 'bootstrap4-error',
    'required_css_class': 'bootstrap4-required',
    'javascript_in_head': True,
    'success_css_class': 'bootstrap4-bound',
}

HTML_MINIFY = True

if os.path.isfile(BASE_DIR / 'config_local.py'):
    from config_local import *  # noqa
