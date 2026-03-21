from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import UserProfile


class AuthenticationTestCase(TestCase):
    """Test authentication functionality"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = Client()
        self.register_url = reverse('register_view')
        self.login_url = reverse('login_view')
        
        # Create test user
        self.test_user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_register_page_loads(self):
        """Test registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
    
    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_user_can_register(self):
        """Test user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!'
        }
        response = self.client.post(self.register_url, data)
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        # Check user was created
        self.assertTrue(UserProfile.objects.filter(username='newuser').exists())
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        # Should redirect to OTP verification
        self.assertEqual(response.status_code, 302)
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')


class UserProfileTestCase(TestCase):
    """Test UserProfile model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))
    
    def test_user_str_method(self):
        """Test user string representation"""
        user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(str(user), 'testuser')
