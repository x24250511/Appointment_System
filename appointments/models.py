import uuid
from django.db import models
from django.contrib.auth.models import User


class Appointment(models.Model):
    """Appointment model with UUID primary key"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='appointments')

    # Industry selection
    INDUSTRY_CHOICES = [
        ('healthcare', 'Healthcare'),
        ('legal', 'Legal Services'),
        ('consultancy', 'Professional Consultancy'),
    ]
    industry = models.CharField(
        max_length=20, choices=INDUSTRY_CHOICES, default='healthcare')

    # Appointment details
    title = models.CharField(max_length=200)
    description = models.TextField()
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    location = models.CharField(max_length=300)

    # Status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    # Email and PDF tracking
    email_sent = models.BooleanField(default=False)
    pdf_generated = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"{self.title} - {self.appointment_date}"


class AppointmentHistory(models.Model):
    """Track all changes to appointments"""

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Appointment histories'

    def __str__(self):
        return f"{self.action} - {self.appointment.title}"
