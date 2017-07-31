#!/usr/bin/env python

"""
Management of Django project
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sm.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:  # noqa
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:  # noqa
            import django  # noqa # pylint: disable=unused-import
        except ImportError:  # noqa
            raise ImportError(  # noqa
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise  # noqa
    execute_from_command_line(sys.argv)
