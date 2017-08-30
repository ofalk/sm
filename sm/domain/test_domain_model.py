import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_0_import(self):
        from domain.models import Domain as DomainModel
        self.assertEqual(DomainModel, DomainModel, 'import went wrong')

    def test_1_creation(self):
        from domain.models import Domain as DomainModel
        status, created = DomainModel.objects.get_or_create(
            name='neverusedXXXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(status, DomainModel,
                              'object not a Location model!?')

    def test_2_name(self):
        from domain.models import Domain as DomainModel
        status = DomainModel.objects.get(name='neverusedXXXX')
        self.assertEqual(status.name, 'neverusedXXXX',
                         'status name not correct')

    def test_3_name__str__(self):
        from domain.models import Domain as DomainModel
        status = DomainModel.objects.get(name='neverusedXXXX')
        self.assertEqual("%s" % status, 'neverusedXXXX',
                         'status name not correct')

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from domain.models import Domain as DomainModel
        try:
            status = DomainModel.objects.get(name='neverusedXXXX')
            status.delete()
        except Exception as e:  # pragma: no cover
            pass  # pragma: no cover


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
