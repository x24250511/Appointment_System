from django.contrib import admin
from .models import Appointment, AppointmentHistory


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'industry', 'appointment_date',
                    'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'industry', 'appointment_date', 'created_at']
    search_fields = ['title', 'description',
                     'location', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    # Enable status change from admin
    list_editable = ['status']

    # Add actions for bulk status changes
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        count = queryset.update(status='confirmed')
        self.message_user(
            request, f'{count} appointment(s) marked as confirmed.')
    mark_confirmed.short_description = 'Mark selected as Confirmed'

    def mark_completed(self, request, queryset):
        count = queryset.update(status='completed')
        self.message_user(
            request, f'{count} appointment(s) marked as completed.')
    mark_completed.short_description = 'Mark selected as Completed'

    def mark_cancelled(self, request, queryset):
        count = queryset.update(status='cancelled')
        self.message_user(
            request, f'{count} appointment(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as Cancelled'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Appointment Details', {
            'fields': ('industry', 'title', 'description', 'appointment_date', 'appointment_time', 'location')
        }),
        ('Status', {
            'fields': ('status', 'email_sent', 'pdf_generated')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['appointment__title', 'notes']
    readonly_fields = ['timestamp']
