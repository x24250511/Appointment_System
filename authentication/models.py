from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime, timedelta


class OTPVerification(models.Model):
    """Store OTP verification attempts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.email} - Verified: {self.is_verified}"

    def is_expired(self):
        return datetime.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"
