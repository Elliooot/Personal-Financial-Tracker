from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid

class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.detail_url = reverse('detail')
        
        username = f'testuser-{uuid.uuid4()}'
        email = f'test-{uuid.uuid4()}@example.com'
        
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
        self.user_credentials = {
            'email': email,
            'password': 'testpass123'
        }
    
    def test_login_page_GET(self):
        """Test that the login page returns a 200 status code and uses the correct template"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_detail_view_requires_login(self):
        """Test that the detail view redirects to the login page if the user is not logged in"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertTrue(response.url.startswith(self.login_url))
    
    def test_logout_redirects_to_login(self):
        """Test that the logout view redirects to the login page"""
        # Log in first
        self.client.login(username=self.user.username, password='testpass123')
        
        # Log out
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertEqual(response.url, self.login_url)

class StatisticsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.statistics_url = reverse('statistics')
        
        # Create a test user
        username = f'testuser-{uuid.uuid4()}'
        email = f'test-{uuid.uuid4()}@example.com'
        
        self.user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
    
    def test_statistics_view_requires_login(self):
        """Test that the statistics view redirects to the login page if the user is not logged in"""
        response = self.client.get(self.statistics_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
    
    def test_statistics_view_accessible_when_logged_in(self):
        """Test that the statistics view is accessible when the user is logged in"""
        # Log in
        self.client.login(username=self.user.username, password='testpass123')
        
        # Access the statistics view
        response = self.client.get(self.statistics_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'statistics.html')

class ManagementViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.management_url = reverse('management')
        
        # Create a test user
        username = f'testuser-{uuid.uuid4()}'
        email = f'test-{uuid.uuid4()}@example.com'
        
        self.user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
    
    def test_management_view_requires_login(self):
        """Test that the management view redirects to the login page if the user is not logged in"""
        response = self.client.get(self.management_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
    
    def test_management_view_accessible_when_logged_in(self):
        """Test that the management view is accessible when the user is logged in"""
        # Log in
        self.client.login(username=self.user.username, password='testpass123')
        
        # Access the management view
        response = self.client.get(self.management_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'management.html')