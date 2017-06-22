DEBUG = True
ADMIN_USERS = ['oliver@linux-kernel.at']
HTML_MINIFY = False
SECRET_KEY = 'c#s9btkc36=@8q^n#!c+%z+ne6*uzy)bc3f+*97^s-c8*f)^+8'
ALLOWED_HOSTS = []   

from sm.settings import INSTALLED_APPS
INSTALLED_APPS.extend([
    'django_extensions',
    'rest_framework',

    'django.contrib.sites',

    'account',
    'social_django',
    'bootstrap4'
])

# Settings for django-bootstrap4
BOOTSTRAP4 = {
    'error_css_class': 'bootstrap4-error',
    'required_css_class': 'bootstrap4-required',
    'javascript_in_head': True,
    'success_css_class': 'bootstrap4-bound',
}

SITE_ID = 1
