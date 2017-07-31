import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class ModelTestCase(unittest.TestCase):
    def test_0_import(self):
        from patchtime.models import Patchtime as PatchtimeModel
        self.assertEqual(PatchtimeModel, PatchtimeModel, 'import went wrong')

    def test_1_creation(self):
        from patchtime.models import Patchtime as PatchtimeModel
        pat, created = PatchtimeModel.objects.get_or_create(
            name='DailyXXXXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(pat, PatchtimeModel,
                              'object not a Patchtime model!?')

    def test_2_name(self):
        from patchtime.models import Patchtime as PatchtimeModel
        pat = PatchtimeModel.objects.get(name='DailyXXXXX')
        self.assertEqual(pat.name, 'DailyXXXXX', 'name not correct')

    def test_3_name__str__(self):
        from patchtime.models import Patchtime as PatchtimeModel
        pat = PatchtimeModel.objects.get(name='DailyXXXXX')
        self.assertEqual("%s" % pat, 'DailyXXXXX', 'name not correct')

    def test_4_delete(self):
        from patchtime.models import Patchtime as PatchtimeModel
        pat = PatchtimeModel.objects.get(name='DailyXXXXX')
        res = pat.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('sm.Patchtime' in res[1])
        self.assertEqual(res[1]['sm.Patchtime'], 1)

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from patchtime.models import Patchtime as PatchtimeModel
        try:
            pat = PatchtimeModel.objects.get(name='DailyXXXXX')
            pat.delete()  # noqa
        except Exception as e:
            pass


if __name__ == '__main__':
    unittest.main()  # noqa
