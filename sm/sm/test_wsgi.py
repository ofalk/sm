import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_0_run_wsgi(self):
        import sm.wsgi
        self.assertEqual(sm.wsgi.application.__class__,
                         django.core.handlers.wsgi.WSGIHandler)

    def tearDownClass():
        """
        Nothing to do here
        """
        pass


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
