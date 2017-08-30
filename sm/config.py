import os
import django.contrib.messages as messages

DEBUG = True
ADMIN_USERS = ['oliver@linux-kernel.at']
HTML_MINIFY = False
SECRET_KEY = 'c#s9btkc36=@8q^n#!c+%z+ne6*uzy)bc3f+*97^s-c8*f)^+8'
ALLOWED_HOSTS = ['sm.dev.linux-kernel.at']

from sm.settings import INSTALLED_APPS  # noqa
INSTALLED_APPS.extend([
  'django_extensions',
  'rest_framework',
  'django.contrib.sites',

  'account',
  'social_django',
  'social.apps.django_app.default',
  'bootstrap3',
  'bootstrap4',
  'debug_toolbar',

  'django_countries',

  'django.contrib.admindocs',

  'whitenoise',

  'sm',
])

from sm.settings import MIDDLEWARE  # noqa
MIDDLEWARE.extend([
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
])

from sm.settings import TEMPLATES  # noqa
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'account.context_processors.account',
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect',
])
TEMPLATES[0]['DIRS'].extend([
  'templates/',
])

# Settings for django-bootstrap4
BOOTSTRAP4 = {
    'error_css_class': 'bootstrap4-error',
    'required_css_class': 'bootstrap4-required',
    'javascript_in_head': True,
    'success_css_class': 'bootstrap4-bound',
}

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
  # 'social.backends.twitter.TwitterOAuth',
  # 'social.backends.google.GoogleOAuth2',
  'social_core.backends.facebook.FacebookOAuth2',
  'account.auth_backends.UsernameAuthenticationBackend',
]

SOCIAL_AUTH_FACEBOOK_KEY = '562669153771397'
SOCIAL_AUTH_FACEBOOK_SECRET = '464b2253199a60acd65ccb254cf84ff1'

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_EMAIL_UNIQUE = True
ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_USE_AUTH_AUTHENTICATE = True
ACCOUNT_LOGIN_REDIRECT_URL = LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# For debug toolbar
INTERNAL_IPS = (
    '127.0.0.1',
    '86.59.13.244',
    '213.129.242.83',
    '213.129.242.84'
)

# Static files configuration (esp. req. during dev.)
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.pardir
    )
)
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = PACKAGE_ROOT
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Required for Bootstrap 3
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}
