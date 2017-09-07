import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_run_wsgi(self):
        import sm.wsgi
        self.assertEqual(sm.wsgi.application.__class__,
                         django.core.handlers.wsgi.WSGIHandler)
