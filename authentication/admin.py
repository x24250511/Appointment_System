from django.contrib import admin
from .models import OTPVerification, UserProfile


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp_code',
                    'is_verified', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email']
    readonly_fields = ['id', 'created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number',
                    'city', 'is_email_verified', 'created_at']
    list_filter = ['is_email_verified', 'city']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
