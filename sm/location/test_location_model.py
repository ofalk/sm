import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class LocationTestCase(unittest.TestCase):
    def test_0_location_import(self):
        from location.models import Location as LocationModel
        self.assertEqual(LocationModel, LocationModel, 'import went wrong')

    def test_1_location_creation(self):
        from location.models import Location as LocationModel
        loc, created = LocationModel.objects.get_or_create(
            name='Virtual123XXX'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(loc, LocationModel,
                              'object not a Location model!?')

    def test_2_location_name(self):
        from location.models import Location as LocationModel
        loc = LocationModel.objects.get(name='Virtual123XXX')
        self.assertEqual(loc.name, 'Virtual123XXX', 'name not correct')

    def test_3_nonexisting_country(self):
        from location.models import Location as LocationModel
        loc = LocationModel.objects.get(name='Virtual123XXX')
        loc.country = 'Mars'
        self.assertEqual(loc.country.flag_url, None)

    def test_4_location_delete(self):
        from location.models import Location as LocationModel
        loc = LocationModel.objects.get(name='Virtual123XXX')
        res = loc.delete()
        self.assertEqual(res[0], 1)
        self.assertTrue('sm.Location' in res[1])
        self.assertEqual(res[1]['sm.Location'], 1)

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from location.models import Location as LocationModel
        try:
            loc = LocationModel.objects.get(name='Virtual123XXX')
            loc.delete()
        except Exception as e:
            pass


if __name__ == '__main__':
    unittest.main()
