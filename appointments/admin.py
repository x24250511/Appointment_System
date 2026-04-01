from django.contrib import admin
from .models import Appointment, AppointmentHistory
from .services import EmailService, PDFService


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'industry', 'appointment_date',
                    'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'industry', 'appointment_date']
    search_fields = ['title', 'description', 'user__username', 'user__email']
    list_editable = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Appointment Information', {
            'fields': ('id', 'user', 'industry', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('appointment_date', 'appointment_time', 'location')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('email_sent', 'pdf_generated', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        """Confirm selected appointments and send email with PDF attachment"""
        count = 0
        for appointment in queryset:
            if appointment.status != 'confirmed':
                appointment.status = 'confirmed'
                appointment.save()

                # Create history record
                AppointmentHistory.objects.create(
                    appointment=appointment,
                    action='confirmed',
                    performed_by=request.user,
                    notes='Appointment confirmed by admin'
                )

                # Generate PDF
                pdf_data = None
                try:
                    pdf_result = PDFService.generate_appointment_pdf(
                        appointment)
                    if pdf_result.get('success'):
                        appointment.pdf_generated = True
                        pdf_data = pdf_result.get('pdf_data')
                        appointment.save()
                        print(
                            f"[PDF] Successfully generated for appointment {appointment.id}")
                except Exception as e:
                    print(f"[PDF] Generation failed: {e}")

                # Send confirmation email with PDF attachment
                try:
                    subject = f"✓ Appointment Confirmed: {appointment.title}"
                    body = f"""Dear {appointment.user.username},

Good news! Your appointment has been confirmed by our team.

Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {appointment.title}
Industry: {appointment.get_industry_display()}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Location: {appointment.location}

Description:
{appointment.description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please arrive 10 minutes early for your appointment.

If you need to reschedule or cancel, please contact us as soon as possible.

Best regards,
SecureFlow Team
"""

                    # Send with or without PDF attachment
                    if pdf_data:
                        result = EmailService.send_email_with_attachment(
                            appointment.user.email,
                            subject,
                            body,
                            pdf_data,
                            f'appointment_{appointment.id}.pdf',
                            from_name="SecureFlow Appointments"
                        )
                    else:
                        result = EmailService.send_email(
                            appointment.user.email,
                            subject,
                            body,
                            from_name="SecureFlow Appointments"
                        )

                    if result.get('success'):
                        appointment.email_sent = True
                        appointment.save()
                        count += 1
                except Exception as e:
                    print(f"Failed to send email: {e}")

        self.message_user(
            request, f'{count} appointment(s) confirmed and emails sent.')
    mark_confirmed.short_description = "✓ Confirm selected appointments"

    def mark_completed(self, request, queryset):
        """Mark selected appointments as completed"""
        updated = queryset.update(status='completed')

        # Create history records
        for appointment in queryset:
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='completed',
                performed_by=request.user,
                notes='Appointment marked as completed by admin'
            )

        self.message_user(
            request, f'{updated} appointment(s) marked as completed.')
    mark_completed.short_description = "✓ Mark as completed"

    def mark_cancelled(self, request, queryset):
        """Cancel selected appointments and notify users"""
        count = 0
        for appointment in queryset:
            if appointment.status != 'cancelled':
                appointment.status = 'cancelled'
                appointment.save()

                # Create history record
                AppointmentHistory.objects.create(
                    appointment=appointment,
                    action='cancelled',
                    performed_by=request.user,
                    notes='Appointment cancelled by admin'
                )

                # Send cancellation email
                try:
                    subject = f"✗ Appointment Cancelled: {appointment.title}"
                    body = f"""Dear {appointment.user.username},

We regret to inform you that your appointment has been cancelled.

Cancelled Appointment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {appointment.title}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Location: {appointment.location}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you would like to reschedule, please create a new appointment through our system.

We apologize for any inconvenience.

Best regards,
SecureFlow Team
"""
                    EmailService.send_email(
                        appointment.user.email, subject, body, from_name="SecureFlow Appointments")
                    count += 1
                except Exception as e:
                    print(f"Failed to send email: {e}")

        self.message_user(
            request, f'{count} appointment(s) cancelled and emails sent.')
    mark_cancelled.short_description = "✗ Cancel selected appointments"


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['appointment__title', 'notes']
    readonly_fields = ['appointment', 'action',
                       'performed_by', 'timestamp', 'changes']
