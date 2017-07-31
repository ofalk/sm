import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_0_status_import(self):
        from status.models import Status as StatusModel
        self.assertEqual(StatusModel, StatusModel, 'import went wrong')

    def test_1_status_creation(self):
        from status.models import Status as StatusModel
        status, created = StatusModel.objects.get_or_create(
            name='neverusedXXXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(status, StatusModel,
                              'object not a Location model!?')

    def test_2_status_name(self):
        from status.models import Status as StatusModel
        status = StatusModel.objects.get(name='neverusedXXXX')
        self.assertEqual(status.name, 'neverusedXXXX',
                         'status name not correct')

    def test_3_status_name__str__(self):
        from status.models import Status as StatusModel
        status = StatusModel.objects.get(name='neverusedXXXX')
        self.assertEqual("%s" % status, 'neverusedXXXX',
                         'status name not correct')

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from status.models import Status as StatusModel
        try:
            status = StatusModel.objects.get(name='neverusedXXXX')
            status.delete()
        except Exception as e:  # pragma: no cover
            pass  # pragma: no cover


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
