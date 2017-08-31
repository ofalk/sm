import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class ServerTestCase(unittest.TestCase):
    def test_0_server_import(self):
        from server.models import Server as ServerModel
        self.assertEqual(ServerModel, ServerModel, 'import went wrong')

    def test_1_server_creation(self):
        from server.models import Server as ServerModel
        server, created = ServerModel.objects.get_or_create(
            hostname='virtualXXX123'
        )
        self.assertEqual(created, True, 'the object was already there?')
        self.assertIsInstance(server, ServerModel,
                              'object not a Location model!?')

    def test_2_server_hostname(self):
        from server.models import Server as ServerModel
        server = ServerModel.objects.get(hostname='virtualXXX123')
        self.assertEqual(server.hostname, 'virtualXXX123',
                         'hostname not correct')

    def test_3_server_hostname__str__(self):
        from server.models import Server as ServerModel
        server = ServerModel.objects.get(hostname='virtualXXX123')
        self.assertEqual("%s" % server, 'virtualXXX123',
                         'hostname not correct')

    def test_4_server_get_absolute_url(self):
        from server.models import Server as ServerModel
        server = ServerModel.objects.get(hostname='virtualXXX123')
        self.assertEqual('/server/%i/' % server.id, server.get_absolute_url(),
                         'reverse url not correct')

    def tearDownClass():
        """
        Make sure we delete our test object at the end
        """
        from server.models import Server as ServerModel
        try:
            server = ServerModel.objects.get(hostname='virtualXXX123')
            server.delete()
        except Exception as e:  # pragma: no cover
            pass  # pragma: no cover


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
