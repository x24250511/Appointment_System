from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from authentication.models import UserProfile
from appointments.models import Appointment


class AppointmentTestCase(TestCase):
    """Test appointment functionality"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = Client()
        
        # Create test user
        self.user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Login the user
        self.client.login(username='testuser', password='TestPass123!')
        
        # URLs
        self.appointment_list_url = reverse('appointment_list')
        self.appointment_create_url = reverse('appointment_create')
    
    def test_appointment_list_page_loads(self):
        """Test appointment list page loads"""
        response = self.client.get(self.appointment_list_url)
        self.assertEqual(response.status_code, 200)
    
    def test_appointment_create_page_loads(self):
        """Test appointment create page loads"""
        response = self.client.get(self.appointment_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Appointment')
    
    def test_create_appointment(self):
        """Test creating an appointment"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            user=self.user,
            industry='healthcare',
            title='Test Appointment',
            description='Test Description',
            appointment_date=tomorrow,
            appointment_time=datetime.strptime('14:00', '%H:%M').time(),
            location='Dublin City Centre Clinic',
            status='pending'
        )
        
        self.assertEqual(appointment.title, 'Test Appointment')
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.status, 'pending')
    
    def test_appointment_requires_authentication(self):
        """Test that appointments require login"""
        self.client.logout()
        response = self.client.get(self.appointment_list_url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/auth/login/'))


class AppointmentModelTestCase(TestCase):
    """Test Appointment model"""
    
    def setUp(self):
        """Create test user"""
        self.user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_appointment_str_method(self):
        """Test appointment string representation"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            user=self.user,
            industry='healthcare',
            title='Doctor Visit',
            description='Annual checkup',
            appointment_date=tomorrow,
            appointment_time=datetime.strptime('10:00', '%H:%M').time(),
            location='Test Location'
        )
        
        self.assertEqual(str(appointment), 'Doctor Visit')
    
    def test_appointment_status_choices(self):
        """Test appointment status choices"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            user=self.user,
            industry='legal',
            title='Legal Consultation',
            description='Contract review',
            appointment_date=tomorrow,
            appointment_time=datetime.strptime('15:00', '%H:%M').time(),
            location='Test Location',
            status='confirmed'
        )
        
        self.assertEqual(appointment.status, 'confirmed')
        self.assertIn(appointment.status, ['pending', 'confirmed', 'cancelled', 'completed'])
