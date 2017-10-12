import os
from stat import S_ISDIR, ST_MODE
try:
    from . settings import DEBUG
except Exception:
    DEBUG = False

import random
import string


def random_string(len=10):
    return ''.join(random.SystemRandom().choice(
        string.ascii_lowercase +
        string.digits) for _ in range(10))


def random_number(start=0, end=10):
    return(random.randint(start, end))


def modules_with_urls():
    """
    Simple function that automatically adds/loads urls from app directories
    (eg. myapp/urls.py will be automatically added)
    This is best called from your projects urls.py
    """
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    selfmod = os.path.basename(os.path.realpath(os.path.dirname(__file__)))
    if DEBUG:
        print("Searching in %s" % path)  # pragma: no cover
    installed = []
    for module in os.listdir(path):
        mode = os.stat(module)[ST_MODE]
        # Skip files
        if not S_ISDIR(mode):
            continue
        # Skip 'self'
        if selfmod == module:
            continue

        if os.path.isfile(os.path.join(module, '__init__.py')):
            if os.path.isfile(os.path.join(module, 'urls.py')):
                if DEBUG:  # pragma: no cover
                    print("Found '%s' module with urls" %
                          module)  # pragma: no cover
                installed.append(module)
            else:
                if DEBUG:
                    print("%s doesn't have urls defined (yet)" %
                          module)  # pragma: no cover
    return installed


def add_to_installed(INSTALLED_APPS):
    for mod in modules_with_urls():
        if mod not in INSTALLED_APPS:
            INSTALLED_APPS.append(mod)
