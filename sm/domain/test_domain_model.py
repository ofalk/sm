import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_0_import(self):
        from domain.models import Domain as Model
        self.assertEqual(Model, Model, 'import went wrong')

    def test_1_creation(self):
        from domain.models import Domain as Model
        item, created = Model.objects.get_or_create(
            name='neverusedXXXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(item, Model, 'object not a Location model!?')

    def test_2_name(self):
        from domain.models import Domain as Model
        item = Model.objects.get(name='neverusedXXXX')
        self.assertEqual(item.name, 'neverusedXXXX', 'status name not correct')

    def test_3_name__str__(self):
        from domain.models import Domain as Model
        item = Model.objects.get(name='neverusedXXXX')
        self.assertEqual("%s" % item, 'neverusedXXXX',
                         'status name not correct')

    def test_4_get_absolute_url(self):
        from domain.models import Domain as Model
        item = Model.objects.get(name='neverusedXXXX')
        self.assertEqual('/domain/detail/%i/' % item.id,
                         item.get_absolute_url(),
                         'reverse url not correct')

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from domain.models import Domain as Model
        try:
            item = Model.objects.get(name='neverusedXXXX')
            item.delete()
        except Exception as e:  # pragma: no cover
            pass  # pragma: no cover


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
