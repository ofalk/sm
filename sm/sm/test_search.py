from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class SearchTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

    def test_search_ajax_nav(self):
        """
        Test that AJAX search returns navigation quick jumps.
        """
        response = self.client.get(reverse('search'), {'q': 'dash', 'ajax': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertTemplateUsed(response, 'search_results_ajax.html')

    def test_search_full_nav(self):
        """
        Test that full search page includes navigation quick jumps.
        """
        response = self.client.get(reverse('search'), {'q': 'server'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Servers')
        self.assertTemplateUsed(response, 'search.html')

    def test_search_too_short(self):
        """
        Test behavior when query is too short.
        """
        response = self.client.get(reverse('search'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Query too short')
