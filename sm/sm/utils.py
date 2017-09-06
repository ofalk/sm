import os
from stat import S_ISDIR, ST_MODE
from sm.settings import DEBUG, INSTALLED_APPS

import random
import string


def random_string(len=10):
    return ''.join(random.SystemRandom().choice(
        string.ascii_lowercase +
        string.digits) for _ in range(10))


def modules_with_urls():
    """
    Simple function that automatically adds/loads urls from app directories
    (eg. myapp/urls.py will be automatically added)
    This is best called from your projects urls.py
    """
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    selfmod = os.path.basename(os.path.realpath(os.path.dirname(__file__)))
    if DEBUG:
        print("Searching in %s" % path)
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
                if DEBUG:
                    print("Found '%s' module with urls" % module)
                installed.append(module)
                # Add to INSTALLED_APPS, since we're already here and have this
                # information at hand
                if module not in INSTALLED_APPS:
                    INSTALLED_APPS.append(module)
            else:
                if DEBUG:
                    print("%s doesn't have urls defined (yet)" % module)
    return installed
